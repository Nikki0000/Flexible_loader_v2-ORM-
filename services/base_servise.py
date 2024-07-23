class BaseService:
    def verify(self, *args, **kwargs):
        raise NotImplementedError("verify method not implemented")

    def load_data(self, *args, **kwargs):
        raise NotImplementedError("load_data method not implemented")
    
    def insert_data(self, *args, **kwargs):
        raise NotImplementedError("insert_data method not implemented")