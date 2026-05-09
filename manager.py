import json
import os

class TaskManager:
    def __init__(self, filename='data/tasks.json'):
        self.filename = filename
        self.ensure_directory()
        self.tasks = self.load_data()

    def ensure_directory(self):
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)

    def load_data(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_data(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=4)

    def add_task(self, user_id, task_name):
        user_id = str(user_id)
        if user_id not in self.tasks:
            self.tasks[user_id] = []
        self.tasks[user_id].append(task_name)
        self.save_data()

    def get_tasks(self, user_id):
        return self.tasks.get(str(user_id), [])
    
    def get_pomodoro_text(self):
        return "Сессия фокуса: 25 минут. Готов начать?"