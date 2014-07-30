from .endpoint import EndpointMixin, endpoint_setup, maybe_quote
from .gerrit_entity import GerritEntity, Self

# gerrit-documentation.googlecode.com/svn/Documentation/2.7/rest-api-accounts.html

class Account(GerritEntity, EndpointMixin):
    _account_id = int
    name = ''
    email = ''

    def endpoint_id(self):
        return (self._account_id or
                maybe_quote(self.email) or
                maybe_quote(self.name))


@endpoint_setup(parent='Account', name='capabilities')
class CapabilityInfo(GerritEntity, EndpointMixin):
    administrateServer = bool
    queryLimit = {str: int}
    createAccount = bool
    createGroup = bool
    createProject = bool
    emailReviewers = bool
    killTask = bool
    viewCaches = bool
    flushCaches = bool
    viewConnections = bool
    viewQueue = bool
    runGC = bool
    startReplication = bool