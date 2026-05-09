import json
import os

class BaseDataManager:
    def __init__(self, filename):
        self.filename = filename
        # Создаем папку data, если её нет
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        
    def load_json(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading JSON: {e}")
            return {}

    def save_json(self, data):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving JSON: {e}")

class TaskManager(BaseDataManager):
    def __init__(self, filename='data/users.json'):
        super().__init__(filename)
        self.data = self.load_json()

    def get_user_data(self, user_id):
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {"tasks": [], "focus_time": 0, "xp": 0, "level": 1}
        
        # Конвертация старых строковых задач в объекты (на всякий случай)
        updated_tasks = []
        for i, task in enumerate(self.data[uid]["tasks"]):
            if isinstance(task, str):
                updated_tasks.append({"id": i, "title": task, "completed": False, "steps": []})
            else:
                updated_tasks.append(task)
        
        self.data[uid]["tasks"] = updated_tasks
        return self.data[uid]

    def add_task(self, user_id, task_name):
        user = self.get_user_data(user_id)
        # Находим максимальный текущий ID и прибавляем 1, чтобы избежать дублей
        next_id = max([t["id"] for t in user["tasks"]], default=-1) + 1
        
        new_task = {
            "id": next_id,
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
                task.setdefault("steps", []).append({"title": step_name, "completed": False})
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

    def delete_task(self, user_id, task_id):
        uid = str(user_id)
        if uid not in self.data:
            return False
            
        initial_count = len(self.data[uid]["tasks"])
        # Фильтруем список, исключая задачу с нужным ID
        self.data[uid]["tasks"] = [t for t in self.data[uid]["tasks"] if t["id"] != task_id]
        
        if len(self.data[uid]["tasks"]) < initial_count:
            self.save_json(self.data)
            return True
        return False

    def add_focus_session(self, user_id, minutes):
        user = self.get_user_data(user_id)
        user["focus_time"] += minutes
        user["xp"] += minutes * 10
        # Каждые 500 XP — новый уровень
        user["level"] = (user["xp"] // 500) + 1 
        self.save_json(self.data)

    def get_user_stats(self, user_id):
        return self.get_user_data(user_id)