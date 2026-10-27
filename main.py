import sys
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt
from database import Database
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox, QTableWidgetItem, QHeaderView, QMessageBox,QInputDialog

from faker import Faker
import random

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('Qt5Agg')

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
    
        uic.loadUi("form.ui", self)
        
        self.db = Database()
        
        self.current_client_id = None
        
        self.setWindowTitle("SimpleCRM")
        self.info_label.setText("Добро пожаловать в CRM систему!")
        
        self.setup_tables()
        
        self.connect_navigation_buttons()
        
        self.connect_action_buttons()
        
        self.load_clients_data()
        
        self.main_stackedWidget.setCurrentIndex(0)  # Страница клиентов = индекс 0

        self.chart_canvases = []
        
    def setup_tables(self):  
        
        # Таблица клиентов
        self.clients_table.setColumnCount(7)
        self.clients_table.setHorizontalHeaderLabels([
            "ID", "ФИО", "Компания", "Телефон", "Сделок", "Прибыль","Информация"])

        self.clients_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.clients_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
    
        self.clients_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.clients_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Таблица сделок
        self.deals_table.setColumnCount(6)
        self.deals_table.setHorizontalHeaderLabels([
            "ID", "Название", "Клиент", "Сумма", "Статус", "Дата создания"])
        # внешний вид таблиц
        self.deals_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.deals_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)

        self.deals_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) 
        self.deals_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
    def connect_navigation_buttons(self):  # Основные кнопки
        self.clients_button.clicked.connect(self.show_all_clients)
        self.deals_button.clicked.connect(self.show_all_deals)
        self.statistic_button.clicked.connect(self.show_statistic_page)
        
        self.back_deals_button.clicked.connect(self.show_all_clients)
        
        self.exit_button.clicked.connect(self.close)
        self.load_test_db_button.clicked.connect(self.load_database)
        self.update_button.clicked.connect(self.update_data)
        self.export_button.clicked.connect(self.export_data)
        self.open_db_button.clicked.connect(self.open_db)
        self.create_db_button.clicked.connect(self.create_db)


    def connect_action_buttons(self): # кнопки для работы с таблицами
        
        self.new_client_button.clicked.connect(self.add_new_client)
        self.change_client_button.clicked.connect(self.edit_client)
        self.delete_client_button.clicked.connect(self.delete_client)
        self.search_clients_button.clicked.connect(self.search_clients)
        self.view_deals_button.clicked.connect(self.view_client_deals)
        
        # Радио-кнопки сортировки клиентов
        self.default_clients_radio.toggled.connect(self.sort_clients)
        self.quantity_clients_radio.toggled.connect(self.sort_clients)
        self.profit_clients_radio.toggled.connect(self.sort_clients)
        
        # Кнопки на странице сделок
        self.new_deal_button.clicked.connect(self.add_new_deal)
        self.change_deal_status_button.clicked.connect(self.change_deal_status)
        self.change_deal_button.clicked.connect(self.edit_deal)
        self.delete_deal_button.clicked.connect(self.delete_deal)
        self.search_deals_button.clicked.connect(self.search_deals)
        
        # Радио-кнопки фильтрации сделок
        self.all_deals_radio.toggled.connect(self.filter_deals)
        self.atwork_deals_radio.toggled.connect(self.filter_deals)
        self.cost_deals_radio.toggled.connect(self.sort_deals_by_cost)
        self.date_deals_radio.toggled.connect(self.sort_deals_by_date)

    #методы клиентов
    
    def load_clients_data(self, sort_by='id'): # Получаем данные из бд и загружаем в таблицу(клиенты)
        clients = self.db.get_all_clients(sort_by)
        self.clients_table.setRowCount(len(clients))
        
        for row_idx, client in enumerate(clients):
            self.clients_table.setItem(row_idx, 0, QTableWidgetItem(str(client['id'])))
            self.clients_table.setItem(row_idx, 1, QTableWidgetItem(client['full_name']))
            self.clients_table.setItem(row_idx, 2, QTableWidgetItem(client['company'] or ''))
            self.clients_table.setItem(row_idx, 3, QTableWidgetItem(client['phone'] or ''))
            self.clients_table.setItem(row_idx, 4, QTableWidgetItem(str(client['deals_count'])))
            self.clients_table.setItem(row_idx, 5, QTableWidgetItem(f"{client['total_profit']:,.2f} ₽"))
    
    def sort_clients(self):
        if self.default_clients_radio.isChecked():
            self.load_clients_data('id')
        elif self.quantity_clients_radio.isChecked():
            self.load_clients_data('deals_count')
        elif self.profit_clients_radio.isChecked():
            self.load_clients_data('total_profit')
    
    def search_clients(self): # поиск клиентов

        search_text = self.search_clients_lineEdit.text().strip()
        if not search_text:
            self.sort_clients()  
            return
            
        clients = self.db.search_clients(search_text)
        self.clients_table.setRowCount(len(clients))
        
        for row_idx, client in enumerate(clients):
            self.clients_table.setItem(row_idx, 0, QTableWidgetItem(str(client['id'])))
            self.clients_table.setItem(row_idx, 1, QTableWidgetItem(client['full_name']))
            self.clients_table.setItem(row_idx, 2, QTableWidgetItem(client['company'] or ''))
            self.clients_table.setItem(row_idx, 3, QTableWidgetItem(client['phone'] or ''))
            self.clients_table.setItem(row_idx, 4, QTableWidgetItem(str(client['deals_count'])))
            self.clients_table.setItem(row_idx, 5, QTableWidgetItem(f"{client['total_profit']:,.2f} ₽"))
    
    def view_client_deals(self): # просмотр сделок конкретного клиента
        selected_rows = self.clients_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента для просмотра сделок")
            return
            
        client_id = int(self.clients_table.item(selected_rows[0].row(), 0).text())
        client_name = self.clients_table.item(selected_rows[0].row(), 1).text()
        
        self.current_client_id = client_id
        self.main_stackedWidget.setCurrentIndex(1) 
        self.load_client_deals(client_id)
        self.info_label.setText(f"Сделки клиента: {client_name}")
    
    def load_client_deals(self, client_id):
        deals = self.db.get_all_deals('все', 'created_date')

        client_deals = [deal for deal in deals if deal['client_id'] == client_id]
        
        self.deals_table.setRowCount(len(client_deals))
        
        for row_idx, deal in enumerate(client_deals):
            self.deals_table.setItem(row_idx, 0, QTableWidgetItem(str(deal['id'])))
            self.deals_table.setItem(row_idx, 1, QTableWidgetItem(deal['title']))
            self.deals_table.setItem(row_idx, 2, QTableWidgetItem(deal['client_name'] or 'Неизвестно'))
            self.deals_table.setItem(row_idx, 3, QTableWidgetItem(f"{deal['amount']:,.2f} ₽"))
            self.deals_table.setItem(row_idx, 4, QTableWidgetItem(deal['status']))
            
            created_date = deal['created_date']
            if isinstance(created_date, str):
                date_str = created_date[:10]  
            else:
                date_str = str(created_date)[:10]
            self.deals_table.setItem(row_idx, 5, QTableWidgetItem(date_str))
    
    def add_new_client(self):
    
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить клиента")
        dialog.setFixedWidth(400)
        
        layout = QVBoxLayout()
        form = QFormLayout()
        
        name_edit = QLineEdit()
        company_edit = QLineEdit()
        phone_edit = QLineEdit()
        notes_edit = QLineEdit()
        
        form.addRow("ФИО *:", name_edit)
        form.addRow("Компания:", company_edit)
        form.addRow("Телефон:", phone_edit)
        form.addRow("Информация:", notes_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not name_edit.text().strip():
                QMessageBox.warning(self, "Ошибка", "ФИО обязательно для заполнения")
                return
                
            client_id = self.db.add_client(
                full_name=name_edit.text().strip(),
                company=company_edit.text().strip(),
                phone=phone_edit.text().strip(),
                notes=notes_edit.text().strip()
            )
            
            if client_id:
                self.load_clients_data()
                self.info_label.setText(f"Клиент добавлен (ID: {client_id})")
                self.update_all_charts()
        
    def edit_client(self):   # редактируем клиента
        selected_rows = self.clients_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента для редактирования")
            return
            
        client_id = int(self.clients_table.item(selected_rows[0].row(), 0).text())
        client = self.db.get_client_by_id(client_id)
        
        if not client:
            QMessageBox.warning(self, "Ошибка", "Клиент не найден")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактировать клиента: {client['full_name']}")
        dialog.setFixedWidth(400)
        
        layout = QVBoxLayout()
        form = QFormLayout()
        
        name_edit = QLineEdit(client['full_name'])
        company_edit = QLineEdit(client['company'] or '')
        email_edit = QLineEdit(client['email'] or '')
        phone_edit = QLineEdit(client['phone'] or '')
        address_edit = QLineEdit(client['address'] or '')
        notes_edit = QLineEdit(client['notes'] or '')
        
        form.addRow("ФИО *:", name_edit)
        form.addRow("Компания:", company_edit)
        form.addRow("Email:", email_edit)
        form.addRow("Телефон:", phone_edit)
        form.addRow("Адрес:", address_edit)
        form.addRow("Заметки:", notes_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not name_edit.text().strip():
                QMessageBox.warning(self, "Ошибка", "ФИО обязательно для заполнения")
                return
                
            updated = self.db.update_client(
                client_id,
                full_name=name_edit.text().strip(),
                company=company_edit.text().strip(),
                email=email_edit.text().strip(),
                phone=phone_edit.text().strip(),
                address=address_edit.text().strip(),
                notes=notes_edit.text().strip()
            )
            
            if updated:
                self.load_clients_data()
                self.info_label.setText(f"Данные клиента обновлены")
    
    def delete_client(self):
        selected_rows = self.clients_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента для удаления")
            return
            
        client_id = int(self.clients_table.item(selected_rows[0].row(), 0).text())
        client_name = self.clients_table.item(selected_rows[0].row(), 1).text()
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить клиента '{client_name}'?\nВсе его сделки также будут удалены.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_client(client_id):
                self.load_clients_data()
                self.info_label.setText(f"Клиент '{client_name}' удален")
                self.update_all_charts()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить клиента")
    
    # методы сделок
    
    def load_deals_data(self, status_filter='все', sort_by='created_date'):

        deals = self.db.get_all_deals(status_filter, sort_by)
        self.deals_table.setRowCount(len(deals))
        
        for row_idx, deal in enumerate(deals):
            self.deals_table.setItem(row_idx, 0, QTableWidgetItem(str(deal['id'])))
            self.deals_table.setItem(row_idx, 1, QTableWidgetItem(deal['title']))
            self.deals_table.setItem(row_idx, 2, QTableWidgetItem(deal['client_name'] or 'Неизвестно'))
            self.deals_table.setItem(row_idx, 3, QTableWidgetItem(f"{deal['amount']:,.2f} ₽"))
            self.deals_table.setItem(row_idx, 4, QTableWidgetItem(deal['status']))
            
            created_date = deal['created_date']
            if isinstance(created_date, str):
                date_str = created_date[:10]
            else:
                date_str = str(created_date)[:10]
            self.deals_table.setItem(row_idx, 5, QTableWidgetItem(date_str))
    
    def filter_deals(self):
        
        if self.current_client_id:
            self.show_all_deals()
            return
            
        if self.all_deals_radio.isChecked():
            self.load_deals_data('все')
        elif self.atwork_deals_radio.isChecked():
            self.load_deals_data('в работе')
    
    def sort_deals_by_cost(self):
        if self.current_client_id:
            self.show_all_deals()
            return
            
        if self.cost_deals_radio.isChecked():
            self.load_deals_data('все', 'amount')
    
    def sort_deals_by_date(self):
        """Сортировка сделок по дате"""
        if self.current_client_id:
            # Если мы в режиме просмотра сделок клиента, возвращаемся ко всем сделкам
            self.show_all_deals()
            return
            
        if self.date_deals_radio.isChecked():
            self.load_deals_data('все', 'created_date')
    
    def search_deals(self):
        search_text = self.search_deals_lineEdit.text().strip()
        
        if self.current_client_id:
            if not search_text:
                self.load_client_deals(self.current_client_id)
                return
                
            deals = self.db.search_deals(search_text)
            client_deals = [deal for deal in deals if deal['client_id'] == self.current_client_id]
            
            self.deals_table.setRowCount(len(client_deals))
            
            for row_idx, deal in enumerate(client_deals):
                self.deals_table.setItem(row_idx, 0, QTableWidgetItem(str(deal['id'])))
                self.deals_table.setItem(row_idx, 1, QTableWidgetItem(deal['title']))
                self.deals_table.setItem(row_idx, 2, QTableWidgetItem(deal['client_name'] or 'Неизвестно'))
                self.deals_table.setItem(row_idx, 3, QTableWidgetItem(f"{deal['amount']:,.2f} ₽"))
                self.deals_table.setItem(row_idx, 4, QTableWidgetItem(deal['status']))
                
                created_date = deal['created_date']
                if isinstance(created_date, str):
                    date_str = created_date[:10]
                else:
                    date_str = str(created_date)[:10]
                self.deals_table.setItem(row_idx, 5, QTableWidgetItem(date_str))
        else:
            if not search_text:
                self.filter_deals()
                return
                
            deals = self.db.search_deals(search_text)
            self.deals_table.setRowCount(len(deals))
            
            for row_idx, deal in enumerate(deals):
                self.deals_table.setItem(row_idx, 0, QTableWidgetItem(str(deal['id'])))
                self.deals_table.setItem(row_idx, 1, QTableWidgetItem(deal['title']))
                self.deals_table.setItem(row_idx, 2, QTableWidgetItem(deal['client_name'] or 'Неизвестно'))
                self.deals_table.setItem(row_idx, 3, QTableWidgetItem(f"{deal['amount']:,.2f} ₽"))
                self.deals_table.setItem(row_idx, 4, QTableWidgetItem(deal['status']))
                
                created_date = deal['created_date']
                if isinstance(created_date, str):
                    date_str = created_date[:10]
                else:
                    date_str = str(created_date)[:10]
                self.deals_table.setItem(row_idx, 5, QTableWidgetItem(date_str))
    
    def add_new_deal(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить сделку")
        dialog.setFixedWidth(400)
        
        layout = QVBoxLayout()
        form = QFormLayout()
        
        title_edit = QLineEdit()
        client_id_edit = QLineEdit()
        amount_edit = QLineEdit()
        description_edit = QLineEdit()
        
        if self.current_client_id:
            client_id_edit.setText(str(self.current_client_id))
            client_id_edit.setEnabled(False) 
        
        status_combo = QComboBox()
        status_combo.addItems(['в работе', 'завершена', 'отменена'])
        
        form.addRow("Название *:", title_edit)
        form.addRow("ID клиента *:", client_id_edit)
        form.addRow("Сумма *:", amount_edit)
        form.addRow("Статус:", status_combo)
        form.addRow("Описание:", description_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not title_edit.text().strip():
                QMessageBox.warning(self, "Ошибка", "Название обязательно")
                return
                
            if not client_id_edit.text().strip():
                QMessageBox.warning(self, "Ошибка", "ID клиента обязательно")
                return
                
            try:
                amount = float(amount_edit.text().replace(',', '.'))
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Сумма должна быть числом")
                return
                
            deal_id = self.db.add_deal(
                client_id=int(client_id_edit.text()),
                title=title_edit.text().strip(),
                amount=amount,
                description=description_edit.text().strip(),
                status=status_combo.currentText()
            )
            
            if deal_id:
                if self.current_client_id:
                    self.load_client_deals(self.current_client_id)
                else:
                    self.filter_deals()
                    
                self.info_label.setText(f"Сделка добавлена (ID: {deal_id})")
                self.update_all_charts()
    
    def change_deal_status(self):
        selected_rows = self.deals_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите сделку для изменения статуса")
            return
            
        deal_id = int(self.deals_table.item(selected_rows[0].row(), 0).text())
        current_status = self.deals_table.item(selected_rows[0].row(), 4).text()
        
       
        statuses = ["в работе", "завершена", "отменена"]
        new_status, ok = QInputDialog.getItem(
            self, "Изменение статуса",
            f"Выберите новый статус для сделки ID: {deal_id}",
            statuses, statuses.index(current_status) if current_status in statuses else 0,
            False
        )
        
        if ok and new_status != current_status:
            if self.db.update_deal_status(deal_id, new_status):
                if self.current_client_id:
                    self.load_client_deals(self.current_client_id)
                else:
                    self.filter_deals()
                    
                self.info_label.setText(f"Статус сделки ID:{deal_id} изменен на '{new_status}'")
                self.update_all_charts()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось изменить статус")
    
    def delete_deal(self):
        selected_rows = self.deals_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите сделку для удаления")
            return
            
        deal_id = int(self.deals_table.item(selected_rows[0].row(), 0).text())
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите удалить выбранную сделку?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_deal(deal_id):
                if self.current_client_id:
                    self.load_client_deals(self.current_client_id)
                else:
                    self.filter_deals()
                    
                self.info_label.setText(f"Сделка ID:{deal_id} удалена")
                self.update_all_charts()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить сделку")

    def edit_deal(self):
        selected_rows = self.deals_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите сделку для редактирования")
            return
            
        deal_id = int(self.deals_table.item(selected_rows[0].row(), 0).text())
        
        deals = self.db.get_all_deals('все', 'created_date')
        deal_info = None
        
        for deal in deals:
            if deal['id'] == deal_id:
                deal_info = deal
                break
        
        if not deal_info:
            QMessageBox.warning(self, "Ошибка", "Сделка не найдена")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактировать сделку: {deal_info['title']}")
        dialog.setFixedWidth(400)
        
        layout = QVBoxLayout()
        form = QFormLayout()
        
        title_edit = QLineEdit(deal_info['title'])
        amount_edit = QLineEdit(str(deal_info['amount']))
        description_edit = QLineEdit(deal_info['description'] or '')
        
        client_id_edit = QLineEdit(str(deal_info['client_id']))
        client_id_edit.setEnabled(False)
        
        status_combo = QComboBox()
        status_combo.addItems(['в работе', 'завершена', 'отменена'])
        
        current_index = status_combo.findText(deal_info['status'])
        if current_index >= 0:
            status_combo.setCurrentIndex(current_index)
        
        form.addRow("Название *:", title_edit)
        form.addRow("ID клиента:", client_id_edit)
        form.addRow("Сумма *:", amount_edit)
        form.addRow("Статус:", status_combo)
        form.addRow("Описание:", description_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not title_edit.text().strip():
                QMessageBox.warning(self, "Ошибка", "Название обязательно")
                return
                
            try:
                amount = float(amount_edit.text().replace(',', '.'))
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Сумма должна быть числом")
                return
            
            reply = QMessageBox.question(
                self, "Подтверждение",
                "Изменить данные сделки?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.db.delete_deal(deal_id)
                
                new_deal_id = self.db.add_deal(
                    client_id=deal_info['client_id'],
                    title=title_edit.text().strip(),
                    amount=amount,
                    description=description_edit.text().strip(),
                    status=status_combo.currentText()
                )
                
                if new_deal_id:
                    if self.current_client_id:#обновляем таблицу
                        self.load_client_deals(self.current_client_id)
                    else:
                        self.filter_deals()
                        
                    self.info_label.setText(f"Сделка обновлена (ID: {new_deal_id})")
    
    # ===== МЕТОДЫ ДЛЯ СТАТИСТИКИ =====
    
    def update_statistics(self):
        stats = self.db.get_statistics()
        
        stats_text = f"""🎯 Всего клиентов: {stats['total_clients']}
💰 Активных сделок: {stats['active_deals']}  
💵 Общий оборот: {stats['total_amount']:,.0f} ₽
📈 Конверсия: {stats['conversion']}%"""
        
        self.statistic_label.setText(stats_text)
          
    def update_all_charts(self):
        if self.main_stackedWidget.currentIndex() == 2:  
            for canvas in self.chart_canvases:
                canvas.deleteLater()
            self.chart_canvases = []
            self.update_statistics()
            self.create_chart1_status()  # Круговая диаграмма
            self.create_chart2_monthly()  # Столбчатый график
            self.create_chart3_top_clients()  # Топ клиентов
        
    def create_chart1_status(self):
        try:
            status_data = self.db.get_deal_status_stats()
            
            fig = Figure(figsize=(4, 3))
            ax = fig.add_subplot(111)
            
            labels = []
            sizes = []
            colors = []
            
            if 'в работе' in status_data:
                labels.append('В работе')
                sizes.append(status_data['в работе'])
                colors.append('#3498db') 
            

            if 'завершена' in status_data:
                labels.append('Завершена')
                sizes.append(status_data['завершена'])
                colors.append('#2ecc71') 
            
  
            if 'отменена' in status_data:
                labels.append('Отменена')
                sizes.append(status_data['отменена'])
                colors.append('#e74c3c') 
            
            if not sizes:
                ax.text(0.5, 0.5, 'Нет данных\nо сделках', 
                       ha='center', va='center', fontsize=12)
                ax.set_title('Статусы сделок')
            else:
                ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                      startangle=90, shadow=True)
                ax.set_title('Статусы сделок')
                ax.axis('equal')  
            
            canvas = FigureCanvas(fig)
            self.chart1_layout = QtWidgets.QVBoxLayout()
            self.chart1_layout.addWidget(canvas)
            self.qwidget1.setLayout(self.chart1_layout)
            self.chart_canvases.append(canvas)
            
        except Exception as e:
            print(f"Ошибка создания графика 1: {e}")
    
    def create_chart2_monthly(self):
        try:
            monthly_data = self.db.get_monthly_profit(6)

            fig = Figure(figsize=(6, 3))
            ax = fig.add_subplot(111)

            months = []
            profits = []
            
            for item in monthly_data:
                month_str = item['month']
                year = month_str[:4]
                month_num = int(month_str[5:7])
                month_names = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
                              'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
                month_label = f"{month_names[month_num-1]} {year[2:]}"
                
                months.append(month_label)
                profits.append(item['total'] or 0)
            
            if not profits:
                ax.text(0.5, 0.5, 'Нет данных\nо прибыли', 
                       ha='center', va='center', fontsize=12)
                ax.set_title('Прибыль по месяцам')
            else:
                bars = ax.bar(months, profits, color='#3498db', edgecolor='black')
                ax.set_title('Прибыль по месяцам (₽)')
                ax.set_ylabel('Сумма (₽)')
                ax.set_xlabel('Месяц')
                
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:,.0f}', ha='center', va='bottom', fontsize=9)
                
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            
            canvas = FigureCanvas(fig)
            self.chart2_layout = QtWidgets.QVBoxLayout()
            self.chart2_layout.addWidget(canvas)
            self.qwidget2.setLayout(self.chart2_layout)
            self.chart_canvases.append(canvas)
            
        except Exception as e:
            print(f"Ошибка создания графика 2: {e}")
    
    def create_chart3_top_clients(self):
        try:
            top_clients = self.db.get_top_clients_chart(5)
            fig = Figure(figsize=(5, 3))
            ax = fig.add_subplot(111)
            names = []
            profits = []
            
            for client in top_clients:
                name = client['full_name']
                if len(name) > 15:
                    name = name[:12] + '...'
                names.append(name)
                profits.append(client['total_profit'] or 0)
            
            if not profits:
                ax.text(0.5, 0.5, 'Нет данных\nо клиентах', 
                       ha='center', va='center', fontsize=12)
                ax.set_title('Топ-5 клиентов')
            else:
                bars = ax.barh(names, profits, color='#9b59b6', edgecolor='black')
                ax.set_title('Топ-5 клиентов по прибыли')
                ax.set_xlabel('Прибыль (₽)')
                
                for bar in bars:
                    width = bar.get_width()
                    if width > 0:
                        ax.text(width, bar.get_y() + bar.get_height()/2.,
                               f' {width:,.0f} ₽', ha='left', va='center', fontsize=9)
            
            fig.tight_layout()
            
            canvas = FigureCanvas(fig)
            self.chart3_layout = QtWidgets.QVBoxLayout()
            self.chart3_layout.addWidget(canvas)
 
            if hasattr(self, 'qwidget3'):
                self.qwidget3.setLayout(self.chart3_layout)
            else:
                self.chart3_label = QtWidgets.QLabel()
                self.chart3_label.setLayout(self.chart3_layout)
               
            
            self.chart_canvases.append(canvas)
            
        except Exception as e:
            print(f"Ошибка создания графика 3: {e}")
        
        
    # ===== МЕТОДЫ НАВИГАЦИИ =====
    
    def show_all_clients(self):
        """Показать всех клиентов"""
        self.current_client_id = None 
        self.main_stackedWidget.setCurrentIndex(0)  
        self.load_clients_data()
        stats = self.db.get_statistics()
        self.info_label.setText(f"Все клиенты. Всего: {stats['total_clients']}")
    
    def show_all_deals(self):
        self.current_client_id = None  
        self.main_stackedWidget.setCurrentIndex(1)   
        self.load_deals_data('все')
        stats = self.db.get_statistics()
        self.info_label.setText(f"Все сделки. Активных: {stats['active_deals']}")

    def show_statistic_page(self):
        self.main_stackedWidget.setCurrentIndex(2)  
        self.update_statistics()
        self.update_all_charts()  
        self.info_label.setText("Статистика системы")
    
    def load_database(self):
        reply = QMessageBox.question(
            self, "Загрузка тестовых данных",
            "Загрузить тестовые данные? Существующие данные будут удалены.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.load_test_data()
            self.load_clients_data()
            self.info_label.setText("Тестовые данные загружены")
            
    def load_test_data(self): # создаём 100 случайных клиентов
        try: 
            fake = Faker('ru_RU')
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM deals")
                cursor.execute("DELETE FROM clients")
            
            client_ids = []
            
            self.info_label.setText("Генерация клиентов...")
            
            for i in range(100):
                client_id = self.db.add_client(
                    full_name=fake.name(),
                    company=fake.company() if random.random() > 0.3 else "",   
                    phone=fake.phone_number(),
                )
                client_ids.append(client_id)
            
            self.info_label.setText("Генерация сделок...")
            
            deal_titles = [
                "Разработка сайта",
                "Техническая поддержка",
                "SEO оптимизация",
                "Контекстная реклама",
                "Дизайн логотипа",
                "Ведение социальных сетей",
                "Настройка CRM системы",
                "Обучение сотрудников",
                "Аудит безопасности",
                "Хостинг и домен",
                "Мобильное приложение",
                "Автоматизация бизнес-процессов",
                "Копирайтинг",
                "Фирменный стиль",
                "Видеопродакшн"
            ]
            
            total_deals = 0
            
            for client_id in client_ids:
                num_deals = random.randint(1, 10)
                
                for deal_num in range(num_deals):
                    title = random.choice(deal_titles)
                    
                    amount = random.randint(5000, 500000)
                    
                    status_chance = random.random()
                    if status_chance < 0.6:   
                        status = "завершена"
                    elif status_chance < 0.9:   
                        status = "в работе"
                    else:  
                        status = "отменена"
                    
                    description = fake.text(max_nb_chars=200)
                    
                    self.db.add_deal(
                        client_id=client_id,
                        title=title,
                        amount=amount,
                        description=description,
                        status=status
                    )
                    
                    total_deals += 1
            
            stats = self.db.get_statistics()
            
            result_message = f"""
    ✅ БД успешно сгенерирована!

    📊 Статистика:
    👥 Клиентов: {stats['total_clients']}
    💰 Сделок: {total_deals}
    💵 Активных сделок: {stats['active_deals']}
    🏦 Общий оборот: {stats['total_amount']:,.0f} ₽
    📈 Конверсия: {stats['conversion']}%
    """
            
            QMessageBox.information(self, "Генерация завершена", result_message)
            

            self.load_clients_data()
            self.info_label.setText(f"Сгенерировано: 100 клиентов, {total_deals} сделок")
            
            return total_deals
            
        except ImportError:
            QMessageBox.critical(
                self, "Ошибка",
                "Библиотека Faker не установлена.\n"
                "Установите её командой:\n"
                "pip install faker"
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сгенерировать БД:\n{str(e)}")
    
    def update_data(self):
        current_index = self.main_stackedWidget.currentIndex()
        
        if current_index == 0:  # Клиенты
            self.load_clients_data()
            self.info_label.setText("Данные клиентов обновлены")
        elif current_index == 1:  # Сделки
            if self.current_client_id:
                self.load_client_deals(self.current_client_id)
                self.info_label.setText("Данные сделок клиента обновлены")
            else:
                self.filter_deals()
                self.info_label.setText("Данные всех сделок обновлены")
        elif current_index == 2:  # Статистика
            self.update_statistics()
            self.info_label.setText("Статистика обновлена")

    def export_data(self):
        try:
            from PyQt6.QtWidgets import QFileDialog, QMessageBox
            import csv
            import os
            from datetime import datetime
            
            folder_path = QFileDialog.getExistingDirectory(
                self, 
                "Выберите папку для сохранения",
                os.path.expanduser("~/Desktop") 
            )
            
            if not folder_path:  
                return
            
            from PyQt6.QtWidgets import QInputDialog
            options = ["Клиентов", "Сделки", "Всё"]
            choice, ok = QInputDialog.getItem(
                self, "Что экспортировать?",
                "Выберите данные для экспорта:",
                options, 0, False
            )
            
            if not ok:
                return
            
            current_date = datetime.now().strftime("%Y-%m-%d")
            
          
            if choice in ["Клиентов", "Всё"]:
                clients = self.db.get_all_clients()
                if clients:
                    clients_file = os.path.join(folder_path, f"clients_{current_date}.csv")
                    with open(clients_file, 'w', newline='', encoding='utf-8-sig') as f:   
                        writer = csv.writer(f, delimiter=';')  
                        
                        writer.writerow([
                            'ID', 'ФИО', 'Компания', 'Телефон', 
                         'Заметки', 'Дата создания', 'Кол-во сделок', 'Общая прибыль'
                        ])
                        
                        # Данные
                        for client in clients:
                            writer.writerow([
                                client['id'],
                                client['full_name'],
                                client['company'] or '',
                                client['phone'] or '',
                                client['notes'] or '',
                                client['created_date'],
                                client['deals_count'],
                                client['total_profit']
                            ])
                    
                    self.info_label.setText(f"Клиенты экспортированы: {os.path.basename(clients_file)}")
            
            if choice in ["Сделки", "Всё"]:
                deals = self.db.get_all_deals('все')
                if deals:
                    deals_file = os.path.join(folder_path, f"deals_{current_date}.csv")
                    with open(deals_file, 'w', newline='', encoding='utf-8-sig') as f:
                        writer = csv.writer(f, delimiter=';')
                        
                        writer.writerow([
                            'ID', 'ID клиента', 'Клиент', 'Название', 'Описание',
                            'Статус', 'Сумма', 'Дата создания', 'Дата закрытия'
                        ])
                        
                        for deal in deals:
                            writer.writerow([
                                deal['id'],
                                deal['client_id'],
                                deal.get('client_name', ''),
                                deal['title'],
                                deal['description'] or '',
                                deal['status'],
                                deal['amount'],
                                deal['created_date'],
                                deal.get('closed_date', '')
                            ])
                    
                    self.info_label.setText(f"Сделки экспортированы: {os.path.basename(deals_file)}")
            
            QMessageBox.information(
                self, "Экспорт завершен",
                f"Файлы сохранены в папку:\n{folder_path}\n\n"
                f"Откройте файлы в Excel для просмотра."
            )
            
            reply = QMessageBox.question(
                self, "Открыть папку?",
                "Открыть папку с экспортированными файлами?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                import subprocess
                import platform
                
                system = platform.system()
                if system == "Windows":
                    os.startfile(folder_path)
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", folder_path])
                else:  # Linux
                    subprocess.run(["xdg-open", folder_path])
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать данные:\n{str(e)}")
        
    def open_db(self):
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Выберите файл базы данных",
                "", 
                "SQLite Database (*.db *.sqlite);;All Files (*.*)"
            )
            
            if file_path:   
                self.db = None
                
                self.db = Database(file_path)
                
                self.update_data()
                
                import os
                db_name = os.path.basename(file_path)
                self.info_label.setText(f"База данных открыта: {db_name}")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть БД:\n{str(e)}")
    
    def create_db(self):
        try:
            from PyQt6.QtWidgets import QFileDialog, QInputDialog
            import os
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Создать новую базу данных",
                "new_database.db",   
                "SQLite Database (*.db);;All Files (*.*)"
            )
            
            if not file_path:
                return  
            
            if not file_path.endswith('.db'):
                file_path += '.db'
            
            if os.path.exists(file_path):
                reply = QMessageBox.question(
                    self, "Файл существует",
                    f"Файл {os.path.basename(file_path)} уже существует.\nПерезаписать?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
            
            reply = QMessageBox.question(
                self, "Тестовые данные",
                "Добавить тестовые данные в новую БД?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        
            self.db = None   
            self.db = Database(file_path)   
         
            if reply == QMessageBox.StandardButton.Yes:
                self.load_test_data()
                self.info_label.setText(f"Создана новая БД с тестовыми данными: {os.path.basename(file_path)}")
            else:
                self.info_label.setText(f"Создана пустая БД: {os.path.basename(file_path)}")
            
            self.show_all_clients()  
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать БД:\n{str(e)}")


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()