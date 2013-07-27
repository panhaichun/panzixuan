class Pagination:

    DEFAULT_PAGE_SIZE = 20
    
    def __init__(self, number, size, total, records):
        if number is None or number < 1:
            raise ValueError('参数[number]不能小于')
        if size is None or size < 1:
            raise ValueError('参数[size]不能小于')
        self.number = number
        self.size = size
        self.total = total
        self.records = []
        if total > ((number - 1) * size):
            self.records.extend(records)
        # 计算总页数
        self.record_count = len(self.records)
        self.total_pages = (total + size - 1) // size

    def has_previous(self):
        return self.number > 1

    def has_next(self):
        return self.number < self.__total_pages

    def get_previous(self):
        return self.number - 1

    def get_next(self):
        return self.number + 1

    def get_first(self):
        return 1

    def get_last(self):
        return self.total_pages
