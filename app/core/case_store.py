"""Durable single-analyst case repository with revision conflicts and hash-chained audit."""
import datetime, hashlib, json, sqlite3, uuid
from contextlib import contextmanager
from pathlib import Path

MAX_SNAPSHOT = 50*1024*1024


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')


class ConflictError(ValueError):pass


class CaseStore:
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, name TEXT NOT NULL, revision INTEGER NOT NULL, snapshot TEXT NOT NULL, sha256 TEXT NOT NULL, updated TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL, revision INTEGER NOT NULL, timestamp TEXT NOT NULL, payload_sha256 TEXT NOT NULL, previous TEXT NOT NULL, digest TEXT NOT NULL)')
        try:self.path.chmod(0o600)
        except OSError:pass

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=15)
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA synchronous=FULL')
        try:
            with db:
                yield db
        finally:
            db.close()

    def save(self,snapshot,case_id=None,expected_revision=0):
        body=canonical(snapshot)
        if len(body)>MAX_SNAPSHOT:raise ValueError('Caso demasiado grande para el piloto local.')
        lab=snapshot.get('lab',{})
        if not isinstance(lab,dict) or not isinstance(lab.get('name'),str) or not lab['name'].strip():raise ValueError('Caso sin laboratorio válido.')
        case_id=str(uuid.UUID(case_id)) if case_id else str(uuid.uuid4())
        digest=hashlib.sha256(body).hexdigest()
        stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT revision FROM cases WHERE id=?',(case_id,)).fetchone()
            revision=row[0] if row else 0
            if revision!=expected_revision:raise ConflictError('El caso cambió en otra sesión. Recupera la versión actual antes de guardar.')
            revision+=1
            db.execute('INSERT INTO cases VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,revision=excluded.revision,snapshot=excluded.snapshot,sha256=excluded.sha256,updated=excluded.updated',(case_id,lab['name'],revision,body.decode(),digest,stamp))
            prev=db.execute('SELECT digest FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
            previous=prev[0] if prev else '0'*64
            event={'case_id':case_id,'revision':revision,'timestamp':stamp,'payload_sha256':digest,'previous':previous}
            audit_digest=hashlib.sha256(canonical(event)).hexdigest()
            db.execute('INSERT INTO audit(case_id,revision,timestamp,payload_sha256,previous,digest) VALUES (?,?,?,?,?,?)',(case_id,revision,stamp,digest,previous,audit_digest))
        return {'case_id':case_id,'revision':revision,'sha256':digest,'updated':stamp}

    def load(self,case_id):
        case_id=str(uuid.UUID(case_id))
        with self.connect() as db:
            row=db.execute('SELECT snapshot,sha256,revision FROM cases WHERE id=?',(case_id,)).fetchone()
        if not row:raise ValueError('Caso inexistente.')
        if not self.verify_audit():raise ValueError('Auditoría del caso no válida.')
        with self.connect() as db:
            event=db.execute('SELECT payload_sha256 FROM audit WHERE case_id=? AND revision=?',(case_id,row[2])).fetchone()
        if not event or event[0]!=row[1]:raise ValueError('Caso no coincide con su auditoría.')
        snapshot=json.loads(row[0])
        if hashlib.sha256(canonical(snapshot)).hexdigest()!=row[1]:raise ValueError('Integridad del caso no válida; no se cargó.')
        return snapshot,row[2]

    def list(self):
        with self.connect() as db:
            return [{'id':r[0],'name':r[1],'revision':r[2],'updated':r[3]} for r in db.execute('SELECT id,name,revision,updated FROM cases ORDER BY updated DESC')]

    def verify_audit(self):
        previous='0'*64
        with self.connect() as db:
            for case_id,revision,stamp,payload,prev,digest in db.execute('SELECT case_id,revision,timestamp,payload_sha256,previous,digest FROM audit ORDER BY seq'):
                event={'case_id':case_id,'revision':revision,'timestamp':stamp,'payload_sha256':payload,'previous':prev}
                if prev!=previous or hashlib.sha256(canonical(event)).hexdigest()!=digest:return False
                previous=digest
        return True
