"""Authorization boundary for a future trusted broker. No inference or credentials.

Not exposed as MCP tools. Caller must be an authenticated native approval adapter.
An ordinary worker cannot create grants. Production brokerage remains disabled.
"""
import json
import math
import secrets
import sqlite3
import time

class Denied(Exception):
    pass

class Authorizations:
    def __init__(self, db):
        self.db = db
        db.execute('''CREATE TABLE IF NOT EXISTS paid_grants (
            token TEXT PRIMARY KEY, identity TEXT, task TEXT, model TEXT,
            data_hash TEXT, max_usd REAL, expires REAL, state TEXT)''')
        db.commit()

    def issue(self, *, identity, task, model, data_hash, max_usd, expires, decision):
        # This function belongs only to the trusted native-confirmation adapter.
        if decision != 'approved' or not math.isfinite(max_usd) or max_usd <= 0 or not math.isfinite(expires) or expires <= time.time():
            raise Denied('approval_required')
        token = secrets.token_urlsafe(32)
        with self.db:
            self.db.execute('INSERT INTO paid_grants VALUES(?,?,?,?,?,?,?,?)',
                (token,identity,task,model,data_hash,max_usd,expires,'approved'))
        return token

    def revoke(self, token):
        with self.db:
            self.db.execute("UPDATE paid_grants SET state='revoked' WHERE token=? AND state='approved'", (token,))

    def consume(self, *, token, identity, task, model, data_hash, max_usd, budget_remaining):
        # Atomic one-use reservation before inference. Crash after consumption never retries.
        if budget_remaining is None or not math.isfinite(budget_remaining) or not math.isfinite(max_usd) or max_usd <= 0 or budget_remaining < max_usd:
            raise Denied('budget_unavailable')
        with self.db:
            count = self.db.execute("""UPDATE paid_grants SET state='consumed'
                WHERE token=? AND identity=? AND task=? AND model=? AND data_hash=?
                AND max_usd>=? AND expires>? AND state='approved'""",
                (token,identity,task,model,data_hash,max_usd,time.time())).rowcount
            if count != 1:
                raise Denied('invalid_expired_or_consumed_grant')
        return {'mode':'DELEGATED','state':'consumed','max_usd':max_usd}


def direct_selection(*, authenticated_identity, selection, server_entitlements):
    """Only the future trusted catalogue adapter calls this, never task text/MCP args.

    Does not ask per-call approval. Server must still enforce key/team budgets.
    It is a contract validator, not an authentication implementation.
    """
    if not authenticated_identity or not selection or not server_entitlements:
        raise Denied('authenticated_selection_required')
    if selection.get('source') != 'native-catalogue' or selection.get('identity') != authenticated_identity:
        raise Denied('explicit_selection_required')
    if selection.get('model') not in server_entitlements.get('models',[]) or not server_entitlements.get('direct_paid'):
        raise Denied('direct_not_entitled')
    if server_entitlements.get('budget_remaining') is None or server_entitlements['budget_remaining'] <= 0:
        raise Denied('budget_unavailable')
    return {'mode':'DIRECT','identity':authenticated_identity,'model':selection['model']}
