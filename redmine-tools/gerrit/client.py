import json
import urllib

from simplemodel import SimpleModelEncoder

from .connection import ClientConnection, HTTPLibConnection
#from .gerrit_entity import keyed_dict

from .accounts import Account, CapabilityInfo
#from .changes import Change, Reviewer, Revision, Draft, Comment, ReviewInput
#from .groups import Group
#from .projects import Project

class Client(object):
    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], ClientConnection):
            self.conn = args[0]
        else:
            self.conn = HTTPLibConnection(*args, **kwargs)
    
    # Accounts
    
    def get_account(self, account):
        return self.get_endpoint(Account, account)

    def get_account_capabilities(self, account):
        return self.get_endpoint(CapabilityInfo, account)

    def check_account_capability(self, account, capability):
        try:
            path = CapabilityInfo.endpoint_path(account, capability)
            self.request(path)
            return True
        except NotFound:
            return False

    def list_groups(self, account):
        return self.get_endpoint(Account, account, result_type=Group)

    def get_avatar_url(self, account):
        path = Account.endpoint_path(account, 'avatar')
        return self.request(path)['Location']

    def get_avatar_change_url(self, account):
        path = Account.endpoint_path(account, 'avatar.change.url')
        return self.request(path).body

    def get_diff_preferences(self, account):
        return self.get_endpoint(Account, account, 'preferences.diff',
                                 result_type=dict)

    def set_diff_preferences(self, account, **prefs):
        return self.put_endpoint(Account, account, 'preferences.diff',
                                 result_type=dict, data=prefs)

    # Changes

    # TODO: support multiple queries
    def query_changes(self, **params):
        return self.get_endpoint(Change, params=params)
        
    def get_change(self, change):
        return self.get_endpoint(Change, change)
        
    def get_change_detail(self, change):
        return self.get_endpoint(Change, change, 'detail')

    def get_topic(self, change):
        return self.get_endpoint(Change, change, 'topic', result_type=unicode)

    def set_topic(self, change, topic):
        return self.put_endpoint(Change, change, 'topic', result_type=unicode,
                                 data={'topic': topic})
            
    def delete_topic(self, change):
        self.delete_endpoint(Change, change, 'topic')
        
    def abandon_change(self, change, message=None):
        if message is not None:
            message = {'message': message}
        return self.post_endpoint(Change, change, 'abandon', data=message)
        
    def restore_change(self, change, message=None):
        if message is not None:
            message = {'message': message}
        return self.post_endpoint(Change, change, 'restore', data=message)

    def revert_change(self, change, message=None):
        if message is not None:
            message = {'message': message}
        return self.post_endpoint(Change, change, 'revert', data=message)

    def submit_change(self, change, wait_for_merge=False):
        if wait_for_merge:
            wait_for_merge = {'wait_for_merge': True}
        return self.post_endpoint(Change, change, 'submit', data=wait_for_merge)

    # Reviewer
        
    def list_reviewers(self, change):
        return self.get_endpoint(Reviewer, change)

    def get_reviewer(self, change, account):
        return self.get_endpoint(Reviewer, change, account)

    def add_reviewer(self, change, account, confirmed=False):
        if isinstance(account, Account):
            account = account.endpoint_id()
        data = {'reviewer': account}
        if confirmed:
            data['confirmed'] = True
        return self.post_endpoint(Reviewer, change, data=data)
        
    def delete_reviewer(self, change, account):
        self.delete_endpoint(Reviewer, change, account)

    # Revision
        
    def get_review(self, change, revision):
        return self.get_endpoint(Revision, change, revision, 'review')

    def set_review(self, change, revision, *args, **kwargs):
        review = ReviewInput(*args, **kwargs)
        return self.post_endpoint(Revision, change, revision, 'review',
                                  data=review)

    def submit_revision(self, change, revision, wait_for_merge=False):
        if wait_for_merge:
            wait_for_merge = {'wait_for_merge': True}
        return self.post_endpoint(Revision, change, revision, 'submit',
                                  data=wait_for_merge, result_type=dict)
    
    def get_submit_type(self, change, revision):
        return self.get_endpoint(Revision, change, revision, 'submit_type',
                                 result_type=str)

    def test_submit_type(self, change, revision, rule, filters=None):
        data = {'rule': rule}
        if filters:
            data['filters'] = filters
        return self.post_endpoint(Revision, change, revision, 'test.submit_type',
                                  data=data, result_type=str)
        
    def test_submit_rule(self, change, revision, rule, filters=None):
        data = {'rule': rule}
        if filters:
            data['filters'] = filters
        return self.post_endpoint(Revision, change, revision, 'test.submit_rule',
                                  data=data, result_type=list)

    def list_drafts(self, change, revision):
        return self.get_endpoint(Draft, change, revision,
                                 result_type=keyed_dict('path', Draft))
        
    def create_draft(self, change, revision, *args, **kwargs):
        draft = Draft(*args, **kwargs)
        return self.put_endpoint(Draft, change, revision, data=draft)

    def get_draft(self, change, revision, draft):
        return self.get_endpoint(Draft, change, revision, draft)
        
    def update_draft(self, change, revision, draft_id, **kwargs):
        if isinstance(draft_id, Draft):
            draft = Draft(draft_id, **kwargs)
            draft_id = draft
        else:
            draft = Draft(**kwargs)
        return self.put_endpoint(Draft, change, revision, draft_id, data=draft)
        
    def delete_draft(self, change, revision, draft):
        self.delete_endpoint(Draft, change, revision, draft)
        
    def list_comments(self, change, revision):
        return self.get_endpoint(Comment, change, revision,
                                 result_type=keyed_dict('path', Comment))
        
    def create_comment(self, change, revision, *args, **kwargs):
        comment = Comment(*args, **kwargs)
        return self.put_endpoint(Comment, change, revision, data=comment)

    def get_comment(self, change, revision, comment):
        return self.get_endpoint(Comment, change, revision, comment)
        
    def set_reviewed(self, change, revision, path):
        self.put_endpoint(Revision, change, revision,
                          'files', path, 'reviewed')
        
    def delete_reviewed(self, change, revision, path):
        self.delete_endpoint(Revision, change, revision,
                             'files', path, 'reviewed')
        
    # TODO: Group

    # Projects
    # TODO: implement all endpoints

    def list_projects(self, **params):
        return self.get_endpoint(Project, params=params,
                                 result_type=keyed_dict('name', Project))
    
    def get_project(self, project):
        return self.get_endpoint(Project, project)

    def get_head(self, project):
        return self.get_endpoint(Project, project, 'HEAD', result_type=unicode)

    def get_repository_statistics(self, project):
        return self.get_endpoint(Project, project, 'statistics.git',
                                 result_type=dict)
        
    def get_config(self, project):
        return self.get_endpoint(Project, project, 'config', result_type=dict)

    # TODO: Dashboard
        
        
    # Helpers
    
    def request(self, path, params=None, data=None, **kwargs):
        if params:
            def sanitize_param(value):
                if isinstance(value, bool):
                    value = int(value)
                return value
            qs = urllib.urlencode([(k, sanitize_param(v))
                                   for k, v in params.iteritems()])
            path = '%s?%s' % (path, qs)

        if data:
            data = json.dumps(data, cls=SimpleModelEncoder)
            
        return self.conn.request(path, data=data, **kwargs)
        
    def get_endpoint(self, cls, *args, **kwargs):
        path = cls.endpoint_path(*args)
        result_type = kwargs.pop('result_type', None)
        
        response = self.request(path, **kwargs)

        if not response.body:
            return

        # Gerrit adds some junk to prevent the JSON from being executable
        body = response.body.lstrip(")]}'\n")
        data = json.loads(body)

        if result_type is None:
            result_type = cls

        if isinstance(data, list) and not issubclass(result_type, list):
            return map(result_type, data)
            
        return result_type(data)

    def put_endpoint(self, *args, **kwargs):
        return self.get_endpoint(*args, method='PUT', **kwargs)
        
    def post_endpoint(self, *args, **kwargs):
        return self.get_endpoint(*args, method='POST', **kwargs)
                        
    def delete_endpoint(self, *args, **kwargs):
        return self.get_endpoint(*args, method='DELETE', **kwargs)