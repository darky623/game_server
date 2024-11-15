class Subject:
    def __init__(self):
        self.observers = []

    def add_observer(self, observer):
        self.observers.append(observer)

    def remove_observer(self, observer):
        self.observers.remove(observer)

    def notify(self, event):
        results = []
        for observer in self.observers:
            result = observer.update(event)
            results.append(result)
        return results