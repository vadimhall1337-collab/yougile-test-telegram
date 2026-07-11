from typing import List, Dict, Any
from yougile.dto.tasks import TaskDto

class TaskTreeService:
    """Сервис для построения иерархического дерева задач."""
    
    def build_visual_tree(self, tasks: List[TaskDto], parent_id: str = None, depth: int = 0) -> List[Dict[str, Any]]:
        """
        Рекурсивно строит плоский список узлов с вычисленными визуальными отступами.
        Возвращает список словарей с DTO задачи и префиксом.
        """
        tree = []
        # Фильтруем задачи текущего уровня (если parent_id None - это корневые задачи)
        current_level_tasks = [t for t in tasks if t.parent_id == parent_id]
        
        for task in current_level_tasks:
            # Формируем отступ: например, 3 пробела на каждый уровень глубины
            indent = "  " * depth
            prefix = f"{indent}☐ " if depth > 0 else "☑️ "
            
            tree.append({
                "task": task,
                "display_text": f"{prefix}{task.title}"
            })
            
            # Рекурсивно ищем подзадачи
            children = self.build_visual_tree(tasks, parent_id=task.id, depth=depth + 1)
            tree.extend(children)
            
        return tree