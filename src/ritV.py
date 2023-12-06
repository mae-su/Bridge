import mysql.connector
import mysql.connector.errors
import pickle
import os
from rich.prompt import Prompt
from rich.console import Console
from src import styles
from src.errors import *
import pyAesCrypt
import os
import io

credential_encryption_key = '1GwtNHOJt1pvBaqAfAvWGnfAhhumKTBinMiVVMjNj2AMXWwYHabkjFo6wewyX5' 
# redundant encryption, a different key is usually used for when the package is encrypted/closed source with all of its functions

class ritV:
	class _QuickConnect(object): # a temporary connnection ot the server
		def __init__(self,inst):
			self.conn = mysql.connector.connect(**inst.db_config)
		
		def __enter__(self):
			return self.conn, self.conn.cursor()

	
		def __exit__(self, exc_type, exc_val, exc_tb):			
			self.conn.close()

	def __init__(self, console:Console,debug=False):
		self.console=console
		self.db_config = {
			'database':'ritV',
			'user':'externalClient',
			'host':'',
			'password':''
		}
		self.debug=debug
		self.db_config["user"]="externalClient"
		self.db_config["database"]="ritV"
		self.active_sessions = {}

		if not os.path.exists('ritv.credentials.aes'): # interactive self setup if db creds are not found
			console.clear()
			if not Prompt.ask('''[underline][bold][orange1]Terms of use:[/orange1][not underline][not bold]
The use of ritV handles sensitive ties between servers and collective actions on accounts. This system exists SOLELY to deter the use of alternative accounts. 
[bold]By using this open-sourced ritV package and/or the database it corresponds to, you agree that:[not bold]
	- The privacy of students' online identities and accounts will be strictly respected.
	- This code will not be used for storing IDs with the intent of general purpose moderation.
	- You agree to the project scopes listed in README.md 
[italic]Type 'Y' to proceed. (y/N)[/italic]''').lower() == 'y':
				console.clear()
				exit()
			console.clear()
			console.print('ritV Self Setup', style=styles.splash)
			while True:
				self.host_name = Prompt.ask('Please enter the database host:',default='localhost',console=console)
				self.db_config["host"]=self.host_name
				
				self.key = Prompt.ask('Please enter the security key',console=console)
				self.db_config["password"]=self.key
				
				console.print(f'Attempting to connect to {self.host_name}... ',style=styles.working,end='')
				if self.verify_connection():
					console.print(f'Success!',style=styles.success)
					break
				else:
					console.print(f'Failed.',style=styles.fail)
			credentials_buffer = io.BytesIO()

			pickle.dump((self.host_name, self.key), credentials_buffer)
			credentials_buffer.seek(0)
			encrypted_buffer = io.BytesIO()
			pyAesCrypt.encryptStream(credentials_buffer, encrypted_buffer, credential_encryption_key, bufferSize=64*1024)
			with open('ritv.credentials.aes', 'wb') as encrypted_file:
				encrypted_buffer.seek(0)
				encrypted_file.write(encrypted_buffer.read())
			
			console.print(f'Credentials have been stored.',style=styles.success)
		else:
			console.clear()
			try:
				with open('ritv.credentials.aes', 'rb') as encrypted_file:
					encrypted_data = encrypted_file.read()
				encrypted_buffer = io.BytesIO(encrypted_data)
				decrypted_buffer = io.BytesIO()
				pyAesCrypt.decryptStream(encrypted_buffer, decrypted_buffer, credential_encryption_key, bufferSize=64*1024)
				decrypted_buffer.seek(0)
				self.host_name, self.key, = pickle.load(decrypted_buffer)

				self.db_config["host"], self.db_config["password"] = self.host_name, self.key
				console.print(f'Testing connection to server ({self.host_name})... ',style=styles.working,end='')
				if self.verify_connection():
					console.print(f'Success!',style=styles.success)
				else:
					console.print(f'Failed to connect.',style=styles.fail)
				
				console.print('ritV is ready.',style=styles.splash)
			except Exception as e:
				console.print(f'Failed to read [link=./ritv.credentials.aes]ritv.credentials.aes[/link]! Please delete the file and re-run.\n  {e}')
			
	def verify_connection(self):
		try:
			conn = mysql.connector.connect(**self.db_config)
			conn.close()
			return True
		except Exception as e:
			print(str(e))
			return False

	def check_banlist(self,id):
		if type(id) is int:
			id=str(id)
		with self._QuickConnect(self) as (conn,cursor):
			query = "SELECT COUNT(*) FROM banned_ids WHERE value = %s"
			cursor.execute(query, (id,))
			count = cursor.fetchone()[0]
			return count > 0

	def fetch_banlist(self):
		with self._QuickConnect(self) as (conn,cursor):
			query = "SELECT value FROM banned_ids"
			cursor.execute(query)
			results = cursor.fetchall()
			banned_ids = [int(row[0]) for row in results]
			return banned_ids
		
		
	def add_to_banlist(self, id): #ty chatgpt
		# Convert id to string if it's an integer
		if type(id) is int:
			id = str(id)

		with self._QuickConnect(self) as (conn, cursor):
			# Check if the ID is already banned
			if not self.check_banlist(id):
				# Prepare the insert query
				query = "INSERT INTO banned_ids (value) VALUES (%s)"
				cursor.execute(query, (id,))

				# Commit the changes to the database
				conn.commit()
				return True
			else:
				# ID is already in the banlist
				return False
			
	def remove_from_banlist(self, id):
		# Convert id to string if it's an integer
		if type(id) is int:
			id = str(id)

		with self._QuickConnect(self) as (conn, cursor):
			# Check if the ID is in the banlist
			if self.check_banlist(id):
				# Prepare the delete query
				query = "DELETE FROM banned_ids WHERE value = %s"
				cursor.execute(query, (id,))

				# Commit the changes to the database
				conn.commit()
				return True
			else:
				# ID is not in the banlist
				return False
