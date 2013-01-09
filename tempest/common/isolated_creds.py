from tempest import exceptions

def get_isolated_creds_common(cls, LOG):
    admin_client = cls._get_identity_admin_client()
    rand_name_root = cls.__name__
    if cls.isolated_creds:
        # Main user already created. Create the alt one...
        rand_name_root += '-alt'
    username = rand_name_root + "-user"
    email = rand_name_root + "@example.com"
    tenant_name = rand_name_root + "-tenant"
    tenant_desc = tenant_name + "-desc"
    password = "pass"
    try:
        resp, tenant = admin_client.create_tenant(name=tenant_name,
            description=tenant_desc)
    except exceptions.Duplicate:
        if cls.config.compute.allow_tenant_reuse:
            tenant = admin_client.get_tenant_by_name(tenant_name)
            LOG.info('Re-using existing tenant %s' % tenant)
        else:
            msg = ('Unable to create isolated tenant %s because ' +
                   'it already exists. If this is related to a ' +
                   'previous test failure, try using ' +
                   'allow_tenant_reuse in tempest.conf') % tenant_name
            raise exceptions.Duplicate(msg)
    try:
        resp, user = admin_client.create_user(username,
            password,
            tenant['id'],
            email)
    except exceptions.Duplicate:
        if cls.config.compute.allow_tenant_reuse:
            user = admin_client.get_user_by_username(tenant['id'],
                username)
            LOG.info('Re-using existing user %s' % user)
        else:
            msg = ('Unable to create isolated user %s because ' +
                   'it already exists. If this is related to a ' +
                   'previous test failure, try using ' +
                   'allow_tenant_reuse in tempest.conf') % tenant_name
            raise exceptions.Duplicate(msg)

    # Store the complete creds (including UUID ids...) for later
    # but return just the username, tenant_name, password tuple
    # that the various clients will use.
    cls.isolated_creds.append((user, tenant))
    return username, tenant_name, password