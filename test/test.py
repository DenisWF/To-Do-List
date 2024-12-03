import logging
import os
import sqlite3
import sys
import threading
import time

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from PyQt6 import uic
from PyQt6.QtCore import QSize, QTime, QDate
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QLabel, \
    QHBoxLayout, QPushButton, QMessageBox, QComboBox, QLineEdit, QTimeEdit, QTabWidget
from plyer import notification


'''class CalendarWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        try:
            uic.loadUi("calendar_window.ui", self)
            print("UI loaded successfully")
        except Exception as e:
            print(f"Error loading UI: {e}")

        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("Calendar Window")
        print("Window initialized")
        print(self.calendarWidget)
        self.calendarWidget.clicked.connect(self.show_tasks_window)
        self.opened_windows = []

        # Создание вкладок для задач и графиков
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        print('showing window')
        self.show()

    def show_tasks_window(self):
        selected_date = self.calendarWidget.selectedDate().toString('yyyy-MM-dd')
        print(f"Selected date: {selected_date}")
        tasks_window = TasksWindow(selected_date)
        tasks_window.show()
        self.opened_windows.append(tasks_window)'''
class CalendarWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("calendar_window.ui", self)
        self.calendarWidget.clicked.connect(self.show_tasks_window)
        self.opened_windows = []

    def show_tasks_window(self, date):
        selected_date = self.calendarWidget.selectedDate().toString('yyyy-MM-dd')
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)
        tasks_window = TasksWindow(selected_date)
        tasks_window.show()
        self.opened_windows.append(tasks_window)

class TasksWindow(QWidget):
    def __init__(self, date):
        super().__init__()
        try:
            ui_file_path = os.path.abspath("tasks_window.ui")
            uic.loadUi(ui_file_path, self)
            print("Tasks UI loaded successfully")
        except Exception as e:
            print(f"Error loading tasks UI: {e}")

        self.selected_date = date
        self.task_list_widget = self.findChild(QListWidget, "taskListWidget")

        self.init_tasks()

        self.add_task_button = self.findChild(QPushButton, "add_task")
        self.add_task_button.clicked.connect(self.add_tasks)

        self.delete_task_button = self.findChild(QPushButton, "delete_task")
        self.delete_task_button.clicked.connect(self.delete_selected_task)

        self.redact_tasks_button = self.findChild(QPushButton, "redact_tasks")
        self.redact_tasks_button.clicked.connect(self.edit_selected_task)

        self.complete_tasks_button = self.findChild(QPushButton, "complete_tasks_button")
        self.complete_tasks_button.clicked.connect(self.show_completed_tasks)

        self.opened_windows = []
        self.button_open_productivity_graph = self.findChild(QPushButton, 'button_open_productivity_graph')
        self.button_open_productivity_graph.clicked.connect(self.open_productivity_graph)

        self.button_open_time_analysis_graph = self.findChild(QPushButton, "button_open_time_analysis_graph")
        self.button_open_time_analysis_graph.clicked.connect(self.open_time_analysis_graph)

    def open_productivity_graph(self):
        # Create and show the productivity graph window
        productivity_graph_window = ProductivityGraph(self.selected_date)
        productivity_graph_window.show()

    def open_time_analysis_graph(self):
        # Create and show the time analysis graph window
        time_analysis_graph_window = TimeAnalysisGraph(self.selected_date)
        time_analysis_graph_window.show()
    def show_completed_tasks(self):
        self.init_tasks(completed=True)

    def init_tasks(self, completed=False):
        self.task_list_widget.clear()

        try:
            sqlite_connection = sqlite3.connect('task.db')
            cursor = sqlite_connection.cursor()

            if completed:
                select_query = """SELECT Название, Важность_задачи, Выполнена_задача, Категория FROM Задачи WHERE Дата = ? AND Выполнена_задача = 'yes'"""
            else:
                select_query = """SELECT Название, Важность_задачи, Выполнена_задача, Категория FROM Задачи WHERE Дата = ?"""

            cursor.execute(select_query, (self.selected_date,))

            tasks = cursor.fetchall()

            for title, priority, completed, category in tasks:
                item_widget = QWidget()
                layout = QHBoxLayout()

                priority_circle = self.set_priority_indicator(priority)

                task_layout = QVBoxLayout()
                title_label = QLabel(title)
                description_label = QLabel(f"Категория: {category}, Выполнена: {'Да' if completed == 'yes' else 'Нет'}")

                task_layout.addWidget(title_label)
                task_layout.addWidget(description_label)

                layout.addWidget(priority_circle)
                layout.addLayout(task_layout)

                item_widget.setLayout(layout)

                list_item = QListWidgetItem()
                list_item.setData(0, title)
                list_item.setSizeHint(item_widget.sizeHint())
                self.task_list_widget.addItem(list_item)
                self.task_list_widget.setItemWidget(list_item, item_widget)

            cursor.close()

        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite", error)

        finally:
            if sqlite_connection:
                sqlite_connection.close()

    def delete_selected_task(self):
        selected_item = self.task_list_widget.currentItem()

        if selected_item:
            task_title = selected_item.data(0)

            reply = QMessageBox.question(self, "Подтвердите удаление",
                                         f"Удалить задачу '{task_title}'?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    sqlite_connection = sqlite3.connect('task.db')
                    cursor = sqlite_connection.cursor()

                    delete_query = """DELETE FROM Задачи WHERE Название = ? AND Дата = ?"""
                    cursor.execute(delete_query, (task_title, self.selected_date))
                    sqlite_connection.commit()
                    cursor.close()

                    self.task_list_widget.takeItem(self.task_list_widget.row(selected_item))

                    QMessageBox.information(self, "Успех", f"Задача '{task_title}' удалена")

                except sqlite3.Error as error:
                    print("Ошибка при работе с SQLite", error)

                finally:
                    if sqlite_connection:
                        sqlite_connection.close()
        else:
            QMessageBox.warning(self, "Предупреждение", "Выберите задачу для удаления")

    def add_tasks(self):
        a_tsk = Add_tasks(self.selected_date)
        a_tsk.show()
        self.opened_windows.append(a_tsk)

    def set_priority_indicator(self, priority):
        priority_circle = QLabel()
        priority_circle.setFixedSize(QSize(15, 15))

        if priority == "high":
            priority_circle.setStyleSheet("background-color: #ff5a1f; border-radius: 7px;")
        elif priority == "medium":
            priority_circle.setStyleSheet("background-color: #fde910; border-radius: 7px;")
        elif priority == "low":
            priority_circle.setStyleSheet("background-color: #00e600; border-radius: 7px;")

        priority_circle.mousePressEvent = lambda event: self.change_priority_color(event, priority_circle)

        return priority_circle

    def change_priority_color(self, event, current_circle):
        current_color = current_circle.styleSheet()

        if "background-color: #ff5a1f" in current_color:
            new_color = "#fde910"
            new_priority = "medium"
        elif "background-color: #fde910" in current_color:
            new_color = "#00e600"
            new_priority = "low"
        elif "background-color: #00e600" in current_color:
            new_color = "#ff5a1f"
            new_priority = "high"

        current_circle.setStyleSheet(f"background-color: {new_color}; border-radius: 7px;")

        selected_item = self.task_list_widget.currentItem()

        if selected_item:
            task_title = selected_item.data(0)

            try:
                sqlite_connection = sqlite3.connect('task.db')
                cursor = sqlite_connection.cursor()

                update_query = """UPDATE Задачи SET Важность_задачи = ? WHERE Название = ? AND Дата = ?"""
                cursor.execute(update_query, (new_priority, task_title, self.selected_date))
                sqlite_connection.commit()
                cursor.close()

            except sqlite3.Error as error:
                print("Ошибка при работе с SQLite", error)

            finally:
                if sqlite_connection:
                    sqlite_connection.close()
        else:
            QMessageBox.warning(self, "Предупреждение", "Выберите задачу для изменения приоритета.")

    def edit_selected_task(self):
        selected_item = self.task_list_widget.currentItem()

        if selected_item:
            task_title = selected_item.data(0)

            redact_window = Redact_task(self.selected_date, task_title)
            redact_window.show()
            self.opened_windows.append(redact_window)
        else:
            QMessageBox.warning(self, "Предупреждение", "Выберите задачу для редактирования")



class Add_tasks(QWidget):
    def __init__(self, selected_date, parent=None):
        super().__init__(parent)
        ui_file_path = os.path.abspath("add_tasks.ui")
        uic.loadUi(ui_file_path, self)

        self.selected_date = selected_date

        self.task_title_input = self.findChild(QLineEdit, "task_title_input")
        self.time_input = self.findChild(QTimeEdit, "time_input")
        self.priority_combo = self.findChild(QComboBox, "prir")
        self.completed_input = self.findChild(QComboBox, "completed_input")
        self.category_input = self.findChild(QLineEdit, "category_input")
        self.apply_task_button = self.findChild(QPushButton, "apply_task_button")
        self.task_title_input = self.findChild(QLineEdit, "task_title_input")

        if self.task_title_input and self.time_input and self.priority_combo and self.category_input:
            print("Все элементы интерфейса найдены!")

        if not self.task_title_input or not self.time_input or not self.priority_combo or not self.category_input:
            print("Ошибка: не удалось найти элементы интерфейса!")

        self.priority_combo.addItems(["high", "medium", "low"])

        self.update_priority_circle()

        self.apply_task_button.clicked.connect(self.add_task_to_db)

    def add_task_to_db(self):
        task_title = self.task_title_input.text()
        task_time = self.time_input.time().toString()
        priority = self.priority_combo.currentText()
        category = self.category_input.text()

        try:
            sqlite_connection = sqlite3.connect('task.db')
            cursor = sqlite_connection.cursor()

            sqlite_insert_query = """INSERT INTO Задачи
                                             (Название, Важность_задачи, Выполнена_задача, Категория, Дата, Время)
                                             VALUES (?, ?, ?, ?, ?, ?);"""
            data_tuple = (task_title, priority, "no", category, self.selected_date, task_time)
            cursor.execute(sqlite_insert_query, data_tuple)
            sqlite_connection.commit()

            cursor.close()

            self.close()
            QMessageBox.information(self, "Успех", "Задача добавлена успешно!")

        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite", error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()

    def update_priority_circle(self):
        selected_priority = self.priority_combo.currentText()

        if selected_priority == "high":
            self.priority_circle.setStyleSheet("background-color: #ff5a1f; border-radius: 7px;")
        elif selected_priority == "medium":
            self.priority_circle.setStyleSheet("background-color: #fde910; border-radius: 7px;")
        elif selected_priority == "low":
            self.priority_circle.setStyleSheet("background-color: #00e600; border-radius: 7px;")

    def change_priority_color(self, event):
        current_color = self.priority_circle.styleSheet()

        if "background-color: #ff5a1f" in current_color:
            self.priority_circle.setStyleSheet("background-color: #fde910; border-radius: 7px;")
            self.priority_combo.setCurrentText("medium")
        elif "background-color: #fde910" in current_color:
            self.priority_circle.setStyleSheet("background-color: #00e600; border-radius: 7px;")
            self.priority_combo.setCurrentText("low")
        elif "background-color: #00e600" in current_color:
            self.priority_circle.setStyleSheet("background-color: #ff5a1f; border-radius: 7px;")
            self.priority_combo.setCurrentText("high")


class Redact_task(QWidget):
    def __init__(self, selected_date, task_title, parent=None):
        super().__init__(parent)
        ui_file_path = os.path.abspath("red_task.ui")
        uic.loadUi(ui_file_path, self)

        self.selected_date = selected_date
        self.task_title = task_title

        self.load_task_data()

        self.name_task = self.findChild(QLineEdit, "name_task")
        self.priority_combo = self.findChild(QComboBox, "priority_combo")
        self.category_input = self.findChild(QLineEdit, "category_input")
        self.completed_input = self.findChild(QComboBox, "completed_input")
        self.time_input = self.findChild(QTimeEdit, "time_input")

        self.name_task.setText(self.task_title)

        self.save_button = self.findChild(QPushButton, "save_button")
        self.save_button.clicked.connect(self.save_task_changes)

    def load_task_data(self):
        try:
            sqlite_connection = sqlite3.connect('task.db')
            cursor = sqlite_connection.cursor()

            select_query = """SELECT Важность_задачи, Категория, Выполнена_задача, Время FROM Задачи WHERE Название = ? AND Дата = ?"""
            cursor.execute(select_query, (self.task_title, self.selected_date))

            task_data = cursor.fetchone()

            if task_data:
                priority, category, completed, time = task_data
                self.priority_combo.setCurrentText(priority)
                self.category_input.setText(category)
                self.completed_input.setCurrentText("Да" if completed == "yes" else "Нет")
                print(time)
                time_str = time
                self.time_input.setTime(QTime.fromString(time_str, "hh:mm:ss"))
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось найти задачу для редактирования")

            cursor.close()

        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite", error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()

    def save_task_changes(self):
        new_name = self.name_task.text()
        new_priority = self.priority_combo.currentText()
        new_category = self.category_input.text()
        new_completed = "yes" if self.completed_input.currentText() == "Да" else "no"
        new_time = self.time_input.time().toString('hh:mm:ss')
        try:
            sqlite_connection = sqlite3.connect('task.db')
            cursor = sqlite_connection.cursor()

            update_query = """UPDATE Задачи SET Название = ?, Важность_задачи = ?, Категория = ?, Выполнена_задача = ?, Время = ?
                              WHERE Название = ? AND Дата = ?"""
            cursor.execute(update_query,
                           (new_name, new_priority, new_category, new_completed, new_time, self.task_title,
                            self.selected_date))
            sqlite_connection.commit()

            cursor.close()

            self.close()

        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite", error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()


class TaskNotifier:
    def __init__(self):
        self.running = True

    def notification_loop(self):
        while self.running:
            current_time = QTime.currentTime().toString("hh:mm:ss")
            current_date = QDate.currentDate().toString("yyyy-MM-dd")

            print(f"Текущее время: {current_time}, текущая дата: {current_date}")

            try:
                sqlite_connection = sqlite3.connect('task.db')
                cursor = sqlite_connection.cursor()

                query = """SELECT Название, Важность_задачи, Категория 
                           FROM Задачи 
                           WHERE Дата = ? AND Время = ? AND Выполнена_задача = 'no'"""
                cursor.execute(query, (current_date, current_time))
                tasks = cursor.fetchall()
                print(f"Найденные задачи: {tasks}")
                cursor.close()

                if tasks:
                    for title, priority, category in tasks:
                        print(f"Отправка уведомления для задачи: {title}")
                        notification.notify(
                            title=f"Напоминание: {title}",
                            message=f"Категория: {category}\nВажность: {priority.capitalize()}",
                            app_name="Task Manager",
                            timeout=10
                        )
                else:
                    print("Задачи не найдены.")

                sqlite_connection.close()

            except sqlite3.Error as error:
                print("Ошибка при работе с SQLite:", error)
            except Exception as ex:
                print("Ошибка в цикле уведомлений:", ex)

            time.sleep(10)

    def start_notification_loop(self):
        print("Запуск цикла уведомлений...")
        threading.Thread(target=self.notification_loop, daemon=True).start()

    def stop(self):
        self.running = False


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="app.log",
    filemode="a"
)


class ProductivityGraph(QWidget):
    def __init__(self, selected_date, parent=None):
        super().__init__(parent)
        self.setWindowTitle("График Продуктивности")

        # Layout for the graph
        self.layout = QVBoxLayout(self)

        # Create the figure and canvas for displaying graph
        self.figure = plt.figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Add the navigation toolbar for matplotlib (optional)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout.addWidget(self.toolbar)

        # Load data and plot the graph
        self.plot_productivity_graph()

    def plot_productivity_graph(self):
        try:
            sqlite_connection = sqlite3.connect('task.db')
            cursor = sqlite_connection.cursor()

            # Query to get the number of tasks completed per day
            query = """
                SELECT Дата, COUNT(*) 
                FROM Задачи 
                WHERE Выполнена_задача = 'yes' 
                GROUP BY Дата
                ORDER BY Дата DESC LIMIT 30;
            """
            cursor.execute(query)
            data = cursor.fetchall()

            if not data:
                return

            # Prepare the data for the plot
            dates = [row[0] for row in data]
            completed_tasks = [row[1] for row in data]

            # Plot the data
            ax = self.figure.add_subplot(111)
            ax.bar(dates, completed_tasks, color='green')

            ax.set_xlabel("Дата")
            ax.set_ylabel("Завершенные задачи")
            ax.set_title("Продуктивность за последние 30 дней")
            plt.xticks(rotation=45, ha="right")

            self.canvas.draw()

        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite:", error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()


class TimeAnalysisGraph(QWidget):
    def __init__(self, selected_date, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Анализ времени по категориям задач")

        # Layout for the graph
        self.layout = QVBoxLayout(self)

        # Create the figure and canvas for displaying graph
        self.figure = plt.figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Add the navigation toolbar for matplotlib (optional)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout.addWidget(self.toolbar)

        # Load data and plot the graph
        self.plot_time_analysis_graph()

    def plot_time_analysis_graph(self):
        try:
            sqlite_connection = sqlite3.connect('task.db')
            cursor = sqlite_connection.cursor()

            # Query to get the total time spent on tasks by category
            query = """
                SELECT Категория, SUM(strftime('%s', Время)) 
                FROM Задачи 
                WHERE Выполнена_задача = 'yes'
                GROUP BY Категория;
            """
            cursor.execute(query)
            data = cursor.fetchall()

            if not data:
                return

            # Prepare the data for the plot
            categories = [row[0] for row in data]
            times = [row[1] for row in data]

            # Convert seconds to hours
            times_in_hours = [time / 3600 for time in times]

            # Plot the data
            ax = self.figure.add_subplot(111)
            ax.pie(times_in_hours, labels=categories, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

            ax.set_title("Время, потраченное по категориям")

            self.canvas.draw()

        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite:", error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()

if __name__ == '__main__':
    notifier = TaskNotifier()
    notifier.start_notification_loop()

    app = QApplication(sys.argv)
    window = CalendarWindow()
    window.show()

    app.aboutToQuit.connect(notifier.stop)

    sys.exit(app.exec())
