class Observer:
    def update(self, event):
        raise NotImplementedError

    def subscribe(self, subject):
        subject.add_observer(self)
