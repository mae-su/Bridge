class EmailFormatException(Exception):
    '''An email passed did not match domain and regex formatting requirements.'''
class BannedEmailException(Exception):
    '''A banned email was excepted.'''
class DuplicateEmailException(Exception):
    '''An existing email was used.'''
class InactiveSessionException(Exception):
    '''No active session was found for the given ID.'''
class AlreadyVerifiedException(Exception):
    '''The ID provided has already been verified and should not go through the verification process again.'''