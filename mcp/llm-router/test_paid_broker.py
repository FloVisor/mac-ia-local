"""Targeted simulation only. No HTTP clients, provider keys or production DB."""
import concurrent.futures
from dataclasses import replace
import json
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from authorization import Denied
from paid_broker import Approval, Client, FinalBill, PaidBroker, PriceBound, TEAM, TEAM_LIMIT, USD, digest

MODEL = 'paid-openrouter/simulated-fixed-model'
PAYLOAD = {'messages': [{'role': 'user', 'content': 'synthetic'}], 'max_output_tokens': 16}


class NativeAuthority:
    def __init__(self):
        self.receipts = {}

    def allow(self, offer, **changes):
        token = secrets.token_urlsafe(16)
        self.receipts[token] = Approval(token, offer['identity'], offer['session'], offer['binding'], 'allow-once', offer['expires'])
        self.receipts[token] = replace(self.receipts[token], **changes)
        return token

    def verify(self, token):
        return self.receipts.get(token)


class Supplier:
    name = 'simulated-supplier'

    def __init__(self):
        self.lock = threading.Lock()
        self.calls = []
        self.quotes = {}
        self.bills = {}
        self.missing_price = False
        self.hard_cap = True
        self.timeout = False
        self.pending = False
        self.breach = False
        self.failed_zero = False
        self.check_reservation = lambda operation: None
        self.paused = None

    def quote(self, model, payload):
        if self.missing_price:
            return None
        p = PriceBound(self.name, model, 'supplier-price-rev-1', digest(payload), 'USD',
                       len(json.dumps(payload).encode()), 1_000, 2_000, 10_000, 10_000,
                       'simulation-only-enforced-hard-cap' if self.hard_cap else '')
        self.quotes[digest(payload)] = p
        return p

    def verify_bound(self, price, payload):
        return self.hard_cap and self.quotes.get(digest(payload)) == price

    def run(self, *, operation, model, payload, price, max_cost_nusd, team, allow_fallback, num_retries):
        self.check_reservation(operation)
        assert self.verify_bound(price, payload) and model == price.model and team == TEAM
        assert set(payload) == {'messages', 'max_output_tokens', 'n'}
        assert payload['n'] == 1 and allow_fallback is False and num_retries == 0
        actual = 0 if self.failed_zero else max_cost_nusd // 2
        if self.breach:
            actual = max_cost_nusd + 1
        with self.lock:
            self.calls.append((operation, max_cost_nusd))
            receipt = secrets.token_urlsafe(16)
            self.bills[receipt] = FinalBill(receipt, operation, self.name, model, price.tariff, TEAM, actual, not self.pending)
        if self.paused:
            self.paused[0].set()
            assert self.paused[1].wait(3)
        if self.timeout:
            raise TimeoutError('synthetic timeout after possible billing')
        return {'text': 'synthetic result', 'bill': receipt}

    def verify_bill(self, receipt):
        return self.bills.get(receipt)


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'paid-ledger.sqlite'
        self.clock = [1000]
        self.native = NativeAuthority()
        self.supplier = Supplier()
        self.credentials = {'pro': Client('openclaw-pro', 'session-pro'), 'perso': Client('openclaw-perso', 'session-perso')}
        # Simulator only: all simulated spenders transact in this same ledger.
        self.coverage = True
        self.broker = self.new_broker()
        self.supplier.check_reservation = self.assert_durable

    def tearDown(self):
        self.tmp.cleanup()

    def new_broker(self):
        return PaidBroker(self.path, authenticate=self.credentials.get,
                          verify_approval=self.native.verify, providers={MODEL: self.supplier},
                          shared_coverage=lambda db, team: self.coverage and team == TEAM,
                          clock=lambda: self.clock[0])

    def assert_durable(self, operation):
        # Independent connection observes the committed claim before supplier.run.
        with sqlite3.connect(self.path) as db:
            row = db.execute('SELECT state,held_nusd FROM operations WHERE id=?', (operation,)).fetchone()
        self.assertEqual(row[0], 'dispatching')
        self.assertGreater(row[1], 0)

    def offer(self, task='task', **kwargs):
        return self.broker.propose('pro', task=task, model=MODEL, payload=PAYLOAD,
                                   **({'cap_nusd': USD, 'expires': 1060} | kwargs))

    def approved(self, task='task'):
        offer = self.offer(task)
        self.broker.approve('pro', offer['operation'], self.native.allow(offer))
        return offer

    def account(self):
        with sqlite3.connect(self.path) as db:
            return db.execute('SELECT spent_nusd,frozen FROM account').fetchone()

    def test_exact_price_and_enforceable_bound_mandatory(self):
        for field in ('missing_price', 'hard_cap'):
            with self.subTest(field=field):
                self.supplier.missing_price = field == 'missing_price'
                self.supplier.hard_cap = field != 'hard_cap'
                with self.assertRaises(Denied):
                    self.offer()
        self.assertEqual(self.supplier.calls, [])

    def test_bad_tariff_and_expiry_rejected(self):
        original = self.supplier.quote
        for change in ({'currency': 'EUR'}, {'provider': 'other'}, {'model': 'other'},
                       {'input_nusd': -1}, {'output_nusd': None}, {'valid_until': 1050}):
            with self.subTest(change=change), patch.object(self.supplier, 'quote', side_effect=lambda m, p: replace(original(m, p), **change)):
                with self.assertRaises(Denied):
                    self.offer()
        self.assertEqual(self.supplier.calls, [])

    def test_all_other_billable_parameters_denied(self):
        for key in ('n', 'tools', 'fallbacks', 'reasoning', 'stream', 'web_search_options', 'service_tier', 'max_tokens'):
            with self.subTest(key=key), self.assertRaises(Denied):
                self.broker.propose('pro', task=key, model=MODEL, payload=PAYLOAD | {key: 2}, cap_nusd=USD, expires=1060)
        for count in (None, True, 0, -1, 4097):
            with self.subTest(count=count), self.assertRaises(Denied):
                self.broker.propose('pro', task=str(count), model=MODEL, payload=PAYLOAD | {'max_output_tokens': count}, cap_nusd=USD, expires=1060)
        self.assertEqual(self.supplier.calls, [])

    def test_approval_attestation_binding_and_identity(self):
        offer = self.offer()
        op = offer['operation']
        with self.assertRaises(Denied):
            self.broker.execute('pro', op)
        for token in ('approved', True, None):
            with self.subTest(token=token), self.assertRaises(Denied):
                self.broker.approve('pro', op, token)
        for change in ({'identity': 'openclaw-perso'}, {'session': 'other'}, {'binding': 'forged'},
                       {'decision': 'allow-always'}, {'decision': 'deny'}, {'expires': 999}):
            with self.subTest(change=change), self.assertRaises(Denied):
                self.broker.approve('pro', op, self.native.allow(offer, **change))
        with self.assertRaises(Denied):
            self.broker.approve('perso', op, self.native.allow(offer))
        with self.assertRaises(Denied):
            self.broker.execute('direct-client', op)
        self.assertEqual(self.supplier.calls, [])

    def test_mutations_need_a_different_native_approval(self):
        offer = self.offer()
        token = self.native.allow(offer)
        changed = self.offer('second-task', cap_nusd=USD // 2)
        with self.assertRaises(Denied):
            self.broker.approve('pro', changed['operation'], token)
        self.assertNotEqual(offer['binding'], changed['binding'])

    def test_expiration_and_revocation_before_dispatch(self):
        offer = self.approved()
        self.clock[0] = 1061
        with self.assertRaises(Denied):
            self.broker.execute('pro', offer['operation'])
        self.clock[0] = 1000
        other = self.approved('other')
        self.assertEqual(self.broker.revoke('pro', other['operation']), 'revoked')
        with self.assertRaises(Denied):
            self.broker.execute('pro', other['operation'])
        self.assertEqual(self.supplier.calls, [])

    def test_operation_and_shared_budget_refusal(self):
        with self.assertRaises(Denied):
            self.offer(cap_nusd=1)
        offer = self.approved()
        with self.broker.transaction() as db:
            db.execute('UPDATE account SET spent_nusd=?', (TEAM_LIMIT - offer['bound_nusd'] + 1,))
        with self.assertRaises(Denied):
            self.broker.execute('pro', offer['operation'])
        self.assertEqual(self.supplier.calls, [])

    def test_reservation_unavailable_or_uncoordinated(self):
        offer = self.approved()
        self.coverage = False
        with self.assertRaises(Denied):
            self.broker.execute('pro', offer['operation'])
        self.coverage = True
        lock = sqlite3.connect(self.path)
        lock.execute('BEGIN IMMEDIATE')
        try:
            with self.assertRaisesRegex(Denied, 'persistent_reservation_unavailable'):
                self.broker.execute('pro', offer['operation'])
        finally:
            lock.rollback()
            lock.close()
        self.assertEqual(self.supplier.calls, [])

    def test_failed_durable_commit_never_calls_supplier(self):
        offer = self.approved()
        original = sqlite3.connect
        class BrokenCommit(sqlite3.Connection):
            def commit(self):
                raise sqlite3.OperationalError('synthetic durable commit failure')
        def connect(*args, **kwargs):
            return original(*args, **kwargs, factory=BrokenCommit)
        with patch('paid_broker.sqlite3.connect', side_effect=connect):
            with self.assertRaisesRegex(Denied, 'persistent_reservation_unavailable'):
                self.broker.execute('pro', offer['operation'])
        self.assertEqual(self.supplier.calls, [])
        self.assertEqual(self.broker.status('pro', offer['operation'])['state'], 'approved')
        self.assertEqual(self.broker.status('pro', offer['operation'])['held_nusd'], 0)

    def test_durable_reservation_and_final_settlement(self):
        offer = self.approved()
        result = self.broker.execute('pro', offer['operation'])
        self.assertEqual(result['billing'], 'settled')
        state = self.new_broker().status('pro', offer['operation'])
        self.assertEqual(state['held_nusd'], 0)
        self.assertEqual(state['actual_nusd'], offer['bound_nusd'] // 2)
        self.assertEqual(self.account(), (state['actual_nusd'], 0))
        receipt = next(iter(self.supplier.bills))
        self.assertTrue(self.broker.reconcile(offer['operation'], receipt))
        self.assertEqual(self.account()[0], state['actual_nusd'])
        with self.assertRaises(Denied):
            self.broker.execute('pro', offer['operation'])
        with self.assertRaises(Denied):
            self.broker.status('perso', offer['operation'])
        self.assertEqual(len(self.supplier.calls), 1)

    def test_concurrent_replay_is_one_execution_across_instances(self):
        offer = self.approved()
        def run(_):
            try:
                self.new_broker().execute('pro', offer['operation'])
                return 1
            except Denied:
                return 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(run, range(8))), 1)
        self.assertEqual(len(self.supplier.calls), 1)

    def test_concurrent_different_operations_cannot_oversubscribe(self):
        offers = [self.approved('task-' + str(i)) for i in range(8)]
        maximum = offers[0]['bound_nusd']
        with self.broker.transaction() as db:
            db.execute('UPDATE account SET spent_nusd=?', (TEAM_LIMIT - maximum,))
        # Timeouts hold the full bound; other offers must not reuse that headroom.
        self.supplier.timeout = True
        def run(offer):
            try:
                self.new_broker().execute('pro', offer['operation'])
            except (Denied, TimeoutError):
                pass
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(run, offers))
        self.assertEqual(len(self.supplier.calls), 1)

    def test_timeout_restart_expiry_and_late_final_bill(self):
        offer = self.approved()
        op = offer['operation']
        self.supplier.timeout = True
        with self.assertRaises(TimeoutError):
            self.broker.execute('pro', op)
        restarted = self.new_broker()
        self.clock[0] = 99999
        self.assertEqual(restarted.status('pro', op)['held_nusd'], offer['bound_nusd'])
        with self.assertRaises(Denied):
            restarted.execute('pro', op)
        self.assertEqual(restarted.revoke('pro', op), 'too_late_reservation_retained')
        self.assertTrue(restarted.reconcile(op, next(iter(self.supplier.bills))))
        self.assertEqual(restarted.status('pro', op)['held_nusd'], 0)
        self.assertEqual(len(self.supplier.calls), 1)

    def test_nonfinal_or_forged_bill_cannot_release(self):
        offer = self.approved()
        self.supplier.pending = True
        self.assertEqual(self.broker.execute('pro', offer['operation'])['billing'], 'uncertain')
        for receipt in ('forged', None):
            with self.assertRaises(Denied):
                self.broker.reconcile(offer['operation'], receipt)
        self.assertEqual(self.broker.status('pro', offer['operation'])['held_nusd'], offer['bound_nusd'])
        self.assertEqual(self.account(), (0, 0))

    def test_revocation_during_dispatch_does_not_release_or_replay(self):
        offer = self.approved()
        started, resume = threading.Event(), threading.Event()
        self.supplier.paused = started, resume
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self.broker.execute, 'pro', offer['operation'])
            try:
                self.assertTrue(started.wait(3))
                self.assertEqual(self.broker.revoke('pro', offer['operation']), 'too_late_reservation_retained')
                self.assertEqual(self.broker.status('pro', offer['operation'])['held_nusd'], offer['bound_nusd'])
            finally:
                resume.set()
            self.assertEqual(future.result()['billing'], 'settled')
        self.assertEqual(len(self.supplier.calls), 1)

    def test_price_changed_after_approval_is_not_silently_requoted(self):
        offer = self.approved()
        self.supplier.quotes.clear()
        with self.assertRaises(Denied):
            self.broker.execute('pro', offer['operation'])
        self.assertEqual(self.supplier.calls, [])

    def test_final_zero_invoice_and_supplier_contract_breach(self):
        zero = self.approved('zero')
        self.supplier.failed_zero = True
        self.broker.execute('pro', zero['operation'])
        self.assertEqual(self.account(), (0, 0))
        self.supplier.failed_zero = False
        self.supplier.breach = True
        bad = self.approved('bad')
        with self.assertRaisesRegex(Denied, 'contract_breach'):
            self.broker.execute('pro', bad['operation'])
        self.assertEqual(self.account(), (bad['bound_nusd'] + 1, 1))
        next_offer = self.approved('after-breach')
        with self.assertRaises(Denied):
            self.broker.execute('pro', next_offer['operation'])
        self.assertEqual(len(self.supplier.calls), 2)

    def test_default_has_no_authority_or_shared_budget_proof(self):
        default = PaidBroker(self.path)
        with self.assertRaises(Denied):
            default.propose('pro', task='not-enabled', model=MODEL, payload=PAYLOAD, cap_nusd=USD, expires=1060)
        offer = self.approved()
        self.broker.shared_coverage = None
        with self.assertRaises(Denied):
            self.broker.execute('pro', offer['operation'])
        self.assertEqual(self.supplier.calls, [])

    def test_contradictory_final_invoice_freezes_account_without_double_charge(self):
        offer = self.approved()
        self.broker.execute('pro', offer['operation'])
        receipt = next(iter(self.supplier.bills))
        actual = self.supplier.bills[receipt].amount_nusd + 1
        self.supplier.bills[receipt] = replace(self.supplier.bills[receipt], amount_nusd=actual)
        with self.assertRaisesRegex(Denied, 'conflicting_final_bill'):
            self.broker.reconcile(offer['operation'], receipt)
        self.assertEqual(self.account(), (actual, 1))
        self.assertTrue(self.broker.reconcile(offer['operation'], receipt))
        self.assertEqual(self.account(), (actual, 1))

    def test_expiration_during_reservation_commit_does_not_dispatch(self):
        offer = self.approved()
        def coverage(db, team):
            self.clock[0] = 1061
            return True
        self.broker.shared_coverage = coverage
        with self.assertRaisesRegex(Denied, 'invalid_before_dispatch'):
            self.broker.execute('pro', offer['operation'])
        self.assertEqual(self.supplier.calls, [])
        self.assertEqual(self.broker.status('pro', offer['operation'])['held_nusd'], offer['bound_nusd'])

    def test_process_death_after_commit_retains_hold_and_prevents_redispatch(self):
        offer = self.approved()
        code = '''import os,sys
from paid_broker import PaidBroker,Client
class Crash:
 name='simulated-supplier'
 def verify_bound(self,price,payload):return True
 def run(self,**kwargs):os._exit(23)
b=PaidBroker(sys.argv[1],authenticate=lambda _:Client('openclaw-pro','session-pro'),
 providers={sys.argv[3]:Crash()},shared_coverage=lambda db,team:True,clock=lambda:1000)
b.execute('pro',sys.argv[2])
'''
        run = subprocess.run([sys.executable, '-c', code, str(self.path), offer['operation'], MODEL],
                             cwd=Path(__file__).parent, capture_output=True, text=True, timeout=5)
        self.assertEqual(run.returncode, 23, run.stderr)
        restarted = self.new_broker()
        state = restarted.status('pro', offer['operation'])
        self.assertEqual(state['state'], 'dispatching')
        self.assertEqual(state['held_nusd'], offer['bound_nusd'])
        with self.assertRaises(Denied):
            restarted.execute('pro', offer['operation'])
        self.assertEqual(self.supplier.calls, [])


if __name__ == '__main__':
    unittest.main()
