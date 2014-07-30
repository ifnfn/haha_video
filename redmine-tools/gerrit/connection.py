try:
    import httplib
except:
    import http.client as httplib
try:
    from urllib.parse import quote, urlparse
except:
    from urllib import quote
    from urlparse import urlparse

class ClientResponse(object):
    def __init__(self, status_code, reason, headers, body):
        self.status_code = int(status_code)
        self.headers = dict(headers)
        self.body = body

        self._lower_headers = {k.lower(): v for k, v in self.headers.iteritems()}
       
    def __getitem__(self, key):
        return self._lower_headers.get(key)
        
            
class ClientError(Exception, ClientResponse): pass
class NotFound(ClientError): pass
            
class ClientConnection(object):
    def __init__(self, base_url, **options):
        self.base_url = base_url.rstrip('/')
        self.options = options
    
    def request(self, path, method='GET', data=None):
        raise NotImplemented


class HTTPLibConnection(ClientConnection):
    def request(self, path, method='GET', data=None):
        scheme, host, base_path = urlparse.urlparse(self.base_url)[:3]
        
        conn = None
        if scheme == 'http':
            conn = httplib.HTTPConnection(host)
        elif scheme == 'https':
            conn = httplib.HTTPSConnection(host)

        full_path = '/'.join([base_path.strip('/'), path])

        headers = {}
        if data:
            headers['Content-Type'] = 'application/json;charset=UTF-8'
        
        conn.request(method, full_path, data, headers)
        http_resp = conn.getresponse()

        resp_cls = ClientResponse
        if http_resp.status == 404:
            resp_cls = NotFound
        elif http_resp.status >= 400:
            resp_cls = ClientError
        
        resp = resp_cls(http_resp.status,
                        http_resp.reason,
                        http_resp.getheaders(),
                        http_resp.read())
        
        conn.close()

        if isinstance(resp, ClientError):
            raise resp

        return resp