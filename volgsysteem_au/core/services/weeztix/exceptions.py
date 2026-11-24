class WeeztixError(Exception):
    """
    Basisexception voor alle fouten binnen de Weeztix-integratie.
    """

class WeeztixAuthenticationError(WeeztixError):
    """
    Authenticatie bij Weeztix is mislukt.
    """

class WeeztixAPIError(WeeztixError):
    """
    Algemene fout tijdens communicatie met de Weeztix API.
    """

class WeeztixConnectionError(WeeztixAPIError):
    """
    De verbinding met Weeztix kon niet worden gemaakt.
    """

class WeeztixHTTPError(WeeztixAPIError):
    """
    Weeztix gaf een niet-succesvolle HTTP-status terug.
    """

class WeeztixResponseError(WeeztixAPIError):
    """
    De response van Weeztix is leeg, ongeldig of kon niet
    correct worden verwerkt.
    """

class WeeztixExportError(WeeztixAPIError):
    """
    Er is een fout opgetreden tijdens de Weeztix-exportworkflow.
    """

class WeeztixExportNotReady(WeeztixExportError):
    """
    De Weeztix-export bestaat, maar is nog niet gereed
    voor download.
    """
class WeeztixTokenCryptoError(WeeztixAuthenticationError):
    """
    Er is een fout opgetreden tijdens het versleutelen
    of ontsleutelen van een Weeztix-token.
    """

