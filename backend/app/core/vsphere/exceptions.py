class VSphereError(Exception):
    pass


class VSphereConnectionError(VSphereError):
    pass


class VSphereObjectNotFoundError(VSphereError):
    pass


class VSphereOperationError(VSphereError):
    pass


class VSphereAuthenticationError(VSphereConnectionError):
    pass


class VSphereTimeoutError(VSphereError):
    pass


class VSphereTaskError(VSphereError):
    pass


class VSpherePermissionError(VSphereError):
    pass
