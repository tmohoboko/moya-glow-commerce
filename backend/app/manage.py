"""Operator-only provisioning. Passwords are read securely, never CLI arguments."""
import argparse
import getpass
import uuid
from .db import ROLE_PERMISSIONS, connection, migrate
from .security import password_hash

parser = argparse.ArgumentParser()
parser.add_argument('command', choices=['create-user','migrate'])
parser.add_argument('--email')
parser.add_argument('--role', choices=list(ROLE_PERMISSIONS), default='customer')
args = parser.parse_args()
migrate()
if args.command == 'create-user':
    if not args.email or '@' not in args.email: parser.error('--email is required')
    password = getpass.getpass('New password (minimum 12 characters): ')
    if len(password)<12: parser.error('Password must contain at least 12 characters')
    with connection() as db:
        db.execute('INSERT INTO users(id,email,password_hash,role) VALUES (?,?,?,?)',(uuid.uuid4().hex,args.email.strip().lower(),password_hash(password),args.role))
    print('User created; no default accounts are provisioned.')
