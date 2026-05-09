import json
import os

class BaseDataManager:
    def __init__(self, filename):
        self.filename = filename
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        
    def load_json(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except: return {}

    def save_json(self, data):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

class TaskManager(BaseDataManager):
    def __init__(self, filename='data/users.json'):
        super().__init__(filename)
        self.data = self.load_json()

    def get_user_data(self, user_id):
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {"tasks": [], "focus_time": 0, "xp": 0, "level": 1}
        
        # Миграция: превращаем старые задачи-строки в словари
        new_tasks = []
        for i, task in enumerate(self.data[uid]["tasks"]):
            if isinstance(task, str):
                new_tasks.append({"id": i, "title": task, "completed": False, "steps": []})
            else:
                new_tasks.append(task)
        self.data[uid]["tasks"] = new_tasks
        return self.data[uid]

    def add_task(self, user_id, task_name):
        user = self.get_user_data(user_id)
        new_task = {
            "id": len(user["tasks"]),
            "title": task_name,
            "completed": False,
            "steps": []
        }
        user["tasks"].append(new_task)
        self.save_json(self.data)

    def add_step(self, user_id, task_id, step_name):
        user = self.get_user_data(user_id)
        for task in user["tasks"]:
            if task["id"] == task_id:
                task["steps"].append({"title": step_name, "completed": False})
                self.save_json(self.data)
                return True
        return False

    def complete_task(self, user_id, task_id):
        user = self.get_user_data(user_id)
        for task in user["tasks"]:
            if task["id"] == task_id:
                task["completed"] = True
                self.save_json(self.data)
                return True
        return False

    def add_focus_session(self, user_id, minutes):
        user = self.get_user_data(user_id)
        user["focus_time"] += minutes
        user["xp"] += minutes * 10
        user["level"] = (user["xp"] // 500) + 1 
        self.save_json(self.data)

    def get_user_stats(self, user_id):
        return self.get_user_data(user_id)