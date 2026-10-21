"""Fail-closed DELEGATED policy core. NOT connected to paid credentials or MCP.

Trusted adapters must attest clients, native one-shot decisions, pinned supplier
prices/cost caps, final bills, and coverage of *all* shared-team spenders. There
are no production adapters. Default construction cannot execute inference.
Money is an integer number of nano-USD; no floating point budget arithmetic.
The SQLite file is this component's own documented ledger, never LiteLLM's DB.
"""
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import stat
import time

from authorization import Denied

TEAM = 'paid-openrouter-shared'
USD = 1_000_000_000
TEAM_LIMIT = 40 * USD
HELD = ('dispatching', 'uncertain')
IDENTITIES = frozenset(('openclaw-pro', 'openclaw-perso'))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def natural(value, *, positive=False):
    if type(value) is not int or value < int(positive) or value > 2**60:
        raise Denied('invalid_integer_bound')
    return value


@dataclass(frozen=True)
class Client:
    identity: str
    session: str


@dataclass(frozen=True)
class PriceBound:
    provider: str
    model: str
    tariff: str
    payload_hash: str
    currency: str
    input_tokens: int  # Attested upper bound on ALL billed input tokens.
    input_nusd: int
    output_nusd: int  # Includes reasoning; no unbounded separate reasoning fee.
    fixed_nusd: int
    valid_until: int
    contract: str  # Trusted adapter's enforceable pinned-price + hard-cap contract.


@dataclass(frozen=True)
class Approval:
    receipt: str
    identity: str
    session: str
    binding: str
    decision: str
    expires: int


@dataclass(frozen=True)
class FinalBill:
    receipt: str
    operation: str
    provider: str
    model: str
    tariff: str
    team: str
    amount_nusd: int
    final: bool


class PaidBroker:
    def __init__(self, ledger, *, authenticate=None, verify_approval=None,
                 providers=None, shared_coverage=None, clock=time.time):
        self.path = Path(ledger)
        self.authenticate = authenticate
        self.verify_approval = verify_approval
        self.providers = dict(providers or {})  # Exact model -> trusted adapter, no pool/fallback.
        self.shared_coverage = shared_coverage
        self.clock = clock
        parent = self.path.parent.lstat()
        if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid()
                or parent.st_mode & 0o077):
            raise Denied('private_ledger_directory_required')
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise Denied('unsafe_ledger')
        finally:
            os.close(fd)
        with self.transaction() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS account (
                team TEXT PRIMARY KEY, limit_nusd INTEGER NOT NULL,
                spent_nusd INTEGER NOT NULL, frozen INTEGER NOT NULL)''')
            db.execute('INSERT OR IGNORE INTO account VALUES(?,?,0,0)', (TEAM, TEAM_LIMIT))
            if db.execute('SELECT limit_nusd FROM account WHERE team=?', (TEAM,)).fetchone()[0] != TEAM_LIMIT:
                raise Denied('shared_budget_contract_changed')
            db.execute('''CREATE TABLE IF NOT EXISTS operations (
                id TEXT PRIMARY KEY, identity TEXT NOT NULL, session TEXT NOT NULL,
                task TEXT NOT NULL, model TEXT NOT NULL, payload TEXT NOT NULL,
                price TEXT NOT NULL, cap_nusd INTEGER NOT NULL, bound_nusd INTEGER NOT NULL,
                expires INTEGER NOT NULL, binding TEXT NOT NULL, state TEXT NOT NULL,
                approval TEXT UNIQUE, held_nusd INTEGER NOT NULL DEFAULT 0,
                actual_nusd INTEGER, bill TEXT UNIQUE,
                UNIQUE(identity,session,task))''')

    @contextmanager
    def transaction(self):
        db = None
        try:
            db = sqlite3.connect(self.path, timeout=2, isolation_level=None)
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA synchronous=FULL')
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()  # Inference is forbidden until this durable commit returns.
        except sqlite3.Error as exc:
            if db is not None:
                db.rollback()
            raise Denied('persistent_reservation_unavailable') from exc
        except BaseException:
            if db is not None:
                db.rollback()
            raise
        finally:
            if db is not None:
                db.close()

    def client(self, credential):
        if self.authenticate is None:
            raise Denied('client_attestation_unavailable')
        ctx = self.authenticate(credential)
        if not isinstance(ctx, Client) or ctx.identity not in IDENTITIES or not ctx.session:
            raise Denied('client_attestation_invalid')
        return ctx

    @staticmethod
    def payload(value):
        # Text only; every extra parameter (tools, n, search, images/audio,
        # cache options, service tier, reasoning budget, fallback, etc.) is denied.
        if (not isinstance(value, dict)
                or set(value) not in ({'messages', 'max_output_tokens'}, {'messages', 'max_output_tokens', 'n'})
                or type(value.get('n', 1)) is not int or value.get('n', 1) != 1):
            raise Denied('unbounded_billable_parameter')
        natural(value['max_output_tokens'], positive=True)
        if value['max_output_tokens'] > 4096:
            raise Denied('output_token_limit')
        messages = value['messages']
        if not isinstance(messages, list) or not messages:
            raise Denied('invalid_messages')
        for msg in messages:
            if (not isinstance(msg, dict) or set(msg) != {'role', 'content'}
                    or msg['role'] not in ('system', 'user', 'assistant')
                    or not isinstance(msg['content'], str)):
                raise Denied('unbounded_billable_input')
        if len(canonical(value).encode()) > 1_000_000:
            raise Denied('input_too_large')
        return json.loads(canonical(value | {'n': 1}))

    def bound(self, model, payload, price, expires):
        provider = self.providers.get(model)
        if provider is None or not isinstance(price, PriceBound):
            raise Denied('exact_supplier_tariff_unavailable')
        for field in ('input_tokens', 'input_nusd', 'output_nusd', 'fixed_nusd', 'valid_until'):
            natural(getattr(price, field))
        if (price.model != model or price.provider != provider.name or not price.tariff
                or not price.contract or price.currency != 'USD'
                or price.payload_hash != digest(payload) or price.valid_until < expires
                or price.valid_until <= self.clock()
                or provider.verify_bound(price, payload) is not True):
            raise Denied('supplier_bound_not_attested')
        cost = (price.input_tokens * price.input_nusd
                + payload['max_output_tokens'] * price.output_nusd + price.fixed_nusd)
        natural(cost, positive=True)
        return cost

    @staticmethod
    def row(db, operation, ctx=None):
        row = db.execute('SELECT * FROM operations WHERE id=?', (operation,)).fetchone()
        if row is None or ctx is not None and (row['identity'], row['session']) != (ctx.identity, ctx.session):
            raise Denied('operation_not_found')
        return dict(row)

    def propose(self, credential, *, task, model, payload, cap_nusd, expires):
        ctx = self.client(credential)
        payload = self.payload(payload)
        natural(cap_nusd, positive=True)
        natural(expires, positive=True)
        if (not isinstance(task, str) or not task or len(task) > 256
                or not isinstance(model, str) or expires <= self.clock()):
            raise Denied('invalid_proposal')
        provider = self.providers.get(model)
        if provider is None:
            raise Denied('exact_supplier_tariff_unavailable')
        # quote() is metadata only: never a generation or billable provider call.
        price = provider.quote(model, payload)
        maximum = self.bound(model, payload, price, expires)
        if maximum > cap_nusd:
            raise Denied('operation_envelope_exceeded')
        operation = secrets.token_urlsafe(24)
        offer = dict(operation=operation, identity=ctx.identity, session=ctx.session,
                     task=task, model=model, payload=payload, price=asdict(price),
                     cap_nusd=cap_nusd, bound_nusd=maximum, expires=expires, team=TEAM)
        binding = digest(offer)
        with self.transaction() as db:
            db.execute('''INSERT INTO operations
                (id,identity,session,task,model,payload,price,cap_nusd,bound_nusd,expires,binding,state)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,'pending')''',
                (operation, ctx.identity, ctx.session, task, model, canonical(payload),
                 canonical(asdict(price)), cap_nusd, maximum, expires, binding))
        return offer | {'binding': binding}

    def approve(self, credential, operation, native_receipt):
        ctx = self.client(credential)
        with self.transaction() as db:
            row = self.row(db, operation, ctx)
            if row['state'] != 'pending' or row['expires'] <= self.clock() or self.verify_approval is None:
                raise Denied('one_shot_native_approval_required')
            # Only the trusted native adapter verifies this receipt. No decision,
            # identity, price or approval boolean supplied by the model is trusted.
            evidence = self.verify_approval(native_receipt)
            if (not isinstance(evidence, Approval) or not evidence.receipt
                    or evidence.decision != 'allow-once' or evidence.binding != row['binding']
                    or evidence.identity != ctx.identity or evidence.session != ctx.session
                    or type(evidence.expires) is not int or evidence.expires <= self.clock()):
                raise Denied('one_shot_native_approval_invalid')
            db.execute("UPDATE operations SET state='approved',approval=?,expires=? WHERE id=?",
                       (evidence.receipt, min(row['expires'], evidence.expires), operation))

    def revoke(self, credential, operation):
        ctx = self.client(credential)
        with self.transaction() as db:
            row = self.row(db, operation, ctx)
            if row['state'] not in ('pending', 'approved'):
                return 'too_late_reservation_retained'
            db.execute("UPDATE operations SET state='revoked' WHERE id=?", (operation,))
            return 'revoked'

    def execute(self, credential, operation):
        ctx = self.client(credential)
        with self.transaction() as db:
            row = self.row(db, operation, ctx)
            if row['state'] != 'approved' or not row['approval'] or row['expires'] <= self.clock():
                raise Denied('approval_expired_revoked_or_consumed')
            payload = self.payload(json.loads(row['payload']))
            price = PriceBound(**json.loads(row['price']))
            maximum = self.bound(row['model'], payload, price, row['expires'])
            if maximum != row['bound_nusd'] or maximum > row['cap_nusd']:
                raise Denied('operation_bound_changed')
            # Coverage must be an attested coordinator contract over this SAME
            # transaction/ledger, including DIRECT. An asynchronous spend read
            # or a caller-supplied balance cannot implement this interface.
            if self.shared_coverage is None or self.shared_coverage(db, TEAM) is not True:
                raise Denied('atomic_shared_budget_coverage_unavailable')
            account = db.execute('SELECT * FROM account WHERE team=?', (TEAM,)).fetchone()
            held = db.execute('SELECT COALESCE(SUM(held_nusd),0) FROM operations').fetchone()[0]
            if account is None or account['limit_nusd'] != TEAM_LIMIT:
                raise Denied('shared_budget_contract_changed')
            natural(account['spent_nusd'])
            natural(held)
            if account['frozen'] or account['spent_nusd'] + held + maximum > account['limit_nusd']:
                raise Denied('shared_envelope_exceeded_or_frozen')
            provider = self.providers[row['model']]
            db.execute("UPDATE operations SET state='dispatching',held_nusd=? WHERE id=?", (maximum, operation))
        # Persisted one-use claim survives process death. No retries, recovery
        # redispatch, fallback or expiry-based release of an in-flight hold.
        try:
            if (self.clock() >= row['expires'] or self.clock() >= price.valid_until
                    or provider.verify_bound(price, payload) is not True):
                raise Denied('approval_or_tariff_invalid_before_dispatch')
            result = provider.run(operation=operation, model=row['model'], payload=payload,
                                  price=price, max_cost_nusd=maximum, team=TEAM,
                                  allow_fallback=False, num_retries=0)
            settled = self.reconcile(operation, result['bill'])
            return {'operation': operation, 'result': result.get('text'),
                    'billing': 'settled' if settled else 'uncertain'}
        except BaseException:
            self.uncertain(operation)
            raise

    def uncertain(self, operation):
        with self.transaction() as db:
            db.execute("UPDATE operations SET state='uncertain' WHERE id=? AND state='dispatching'", (operation,))

    def reconcile(self, operation, receipt):
        # Privileged billing adapter only; a response body or timeout alone is
        # never evidence that billing is final, including a zero-cost failure.
        conflict = breach = False
        with self.transaction() as db:
            row = self.row(db, operation)
            provider = self.providers.get(row['model'])
            if provider is None:
                raise Denied('billing_verifier_unavailable')
            bill = provider.verify_bill(receipt)
            price = PriceBound(**json.loads(row['price']))
            if (not isinstance(bill, FinalBill) or not bill.receipt
                    or (bill.operation, bill.provider, bill.model, bill.tariff, bill.team)
                    != (operation, price.provider, row['model'], price.tariff, TEAM)):
                raise Denied('billing_attestation_invalid')
            natural(bill.amount_nusd)
            if bill.final is not True:
                if row['state'] == 'dispatching':
                    db.execute("UPDATE operations SET state='uncertain' WHERE id=?", (operation,))
                return False
            if row['state'] in ('settled', 'breach'):
                if (row['bill'], row['actual_nusd']) != (bill.receipt, bill.amount_nusd):
                    # An allegedly immutable final bill changed: freeze, retain
                    # the larger known liability, and commit before reporting.
                    actual = max(row['actual_nusd'], bill.amount_nusd)
                    db.execute('UPDATE account SET frozen=1,spent_nusd=spent_nusd+? WHERE team=?',
                               (actual - row['actual_nusd'], TEAM))
                    db.execute("UPDATE operations SET state='breach',actual_nusd=? WHERE id=?", (actual, operation))
                    conflict = True
                else:
                    return True
            else:
                if row['state'] not in HELD:
                    raise Denied('no_persistent_reservation')
                breach = bill.amount_nusd > row['held_nusd']
                db.execute('UPDATE account SET spent_nusd=spent_nusd+?,frozen=MAX(frozen,?) WHERE team=?',
                           (bill.amount_nusd, int(breach), TEAM))
                db.execute('UPDATE operations SET state=?,held_nusd=0,actual_nusd=?,bill=? WHERE id=?',
                           ('breach' if breach else 'settled', bill.amount_nusd, bill.receipt, operation))
        if conflict:
            raise Denied('conflicting_final_bill_account_frozen')
        if breach:
            raise Denied('supplier_cost_contract_breach_account_frozen')
        return True

    def status(self, credential, operation):
        ctx = self.client(credential)
        with self.transaction() as db:
            row = self.row(db, operation, ctx)
            return {k: row[k] for k in ('id', 'state', 'held_nusd', 'actual_nusd', 'bound_nusd', 'cap_nusd')}
