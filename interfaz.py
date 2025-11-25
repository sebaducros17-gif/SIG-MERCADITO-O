import sys
import os
import pymysql
from datetime import datetime

# INTERFAZ GRAFICA
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QMessageBox, QInputDialog, QShortcut, QTabWidget, 
                             QDateEdit, QComboBox, QGroupBox, QFormLayout, QDialog)
from PyQt5.QtGui import QFont, QColor, QKeySequence, QPalette
from PyQt5.QtCore import Qt, QDate

# GRAFICOS
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# PDF (TICKET)
from reportlab.pdfgen import canvas


DB_CONFIG = {
    'host': 'localhost', 
    'user': 'root', 
    'password': '$Adb4242',  
    'database': 'mercadito_o'
}

# =======================================================
# UTILIDAD: TICKET PDF
# =======================================================
def generar_ticket_pdf(id_venta, items, total, usuario, metodo):
    nombre = f"ticket_{id_venta}.pdf"
    try:
        c = canvas.Canvas(nombre, pagesize=(300, 600 + (len(items)*20)))
        y = c._pagesize[1] - 20
        
        c.setFont("Helvetica-Bold", 14); c.drawCentredString(150, y, "MERCADITO 'O'"); y-=20
        c.setFont("Helvetica", 10); c.drawCentredString(150, y, "Comprobante de Venta"); y-=25
        
        c.drawString(10, y, f"Fecha: {datetime.now().strftime('%d/%m %H:%M')}"); y-=15
        c.drawString(10, y, f"Ticket: {id_venta}"); y-=15
        c.drawString(10, y, f"Cajero: {usuario}"); y-=25
        
        c.setFont("Helvetica-Bold", 9); c.drawString(10, y, "Cant x Producto"); c.drawRightString(280, y, "Total"); y-=5
        c.line(10, y, 290, y); y-=15
        
        c.setFont("Helvetica", 9)
        for it in items:
            nom = it['nom'][:25]
            dto = it.get('descuento', 0)
            desc_txt = f"(Dto {int(dto*100)}%)" if dto > 0 else ""
            linea = f"{it['cant']:.2f} x {nom} {desc_txt}"
            c.drawString(10, y, linea)
            c.drawRightString(280, y, f"${int(it['sub']):,}")
            y-=15
        
        c.line(10, y, 290, y); y-=20
        c.setFont("Helvetica-Bold", 16)
        c.drawString(10, y, "TOTAL:"); c.drawRightString(280, y, f"${int(total):,}"); y-=25
        c.setFont("Helvetica", 10); c.drawString(10, y, f"Pago: {metodo}"); y-=30
        c.drawCentredString(150, y, "¡Gracias por su compra!"); c.save()
        os.startfile(nombre)
    except: pass

# =======================================================
# LOGIN (CORREGIDO)
# =======================================================
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Acceso")
        self.setFixedSize(300, 180)
        self.usuario_logueado = None # <--- ESTO FALTABA ANTES
        
        l = QVBoxLayout(self)
        self.u = QLineEdit(); self.u.setPlaceholderText("Usuario")
        self.p = QLineEdit(); self.p.setPlaceholderText("Contraseña"); self.p.setEchoMode(QLineEdit.Password)
        
        b = QPushButton("ENTRAR")
        b.setStyleSheet("background:#2E7D32;color:white;font-weight:bold;padding:8px")
        b.clicked.connect(self.validar)
        
        l.addWidget(QLabel("<h2>Bienvenido</h2>", alignment=Qt.AlignCenter))
        l.addWidget(self.u)
        l.addWidget(self.p)
        l.addWidget(b)
    
    def validar(self):
        try:
            conn = pymysql.connect(**DB_CONFIG)
            c = conn.cursor()
            c.execute("SELECT usuario FROM usuarios WHERE usuario=%s AND password=%s", (self.u.text(), self.p.text()))
            r = c.fetchone()
            conn.close()
            
            if r: 
                self.usuario_logueado = r[0] # <--- ASIGNACION CORRECTA
                self.accept()
            else: 
                QMessageBox.warning(self, "Error", "Datos incorrectos")
        except Exception as e: 
            QMessageBox.critical(self, "Error", f"Error SQL: {e}")

class SelectorProductoDialog(QDialog):
    def __init__(self, prods):
        super().__init__()
        self.setWindowTitle("Seleccionar")
        self.setFixedSize(600, 400)
        self.sel = None
        self.prods = prods
        
        l = QVBoxLayout(self)
        l.addWidget(QLabel("Múltiples resultados. Elija uno:"))
        self.t = QTableWidget(); self.t.setColumnCount(4)
        self.t.setHorizontalHeaderLabels(["SKU","Nombre","Precio","Stock"])
        self.t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.t.setSelectionBehavior(QTableWidget.SelectRows)
        self.t.setSelectionMode(QTableWidget.SingleSelection)
        self.t.doubleClicked.connect(self.ok)
        l.addWidget(self.t)
        
        self.load()
    
    def load(self):
        self.t.setRowCount(0)
        for i, p in enumerate(self.prods):
            self.t.insertRow(i)
            self.t.setItem(i,0,QTableWidgetItem(str(p[0])))
            self.t.setItem(i,1,QTableWidgetItem(str(p[1])))
            self.t.setItem(i,2,QTableWidgetItem(f"${float(p[2]):,.0f}"))
            self.t.setItem(i,3,QTableWidgetItem(str(p[4])))
    
    def ok(self):
        r = self.t.currentRow()
        if r >= 0: 
            self.sel = self.prods[r]
            self.accept()

# =======================================================
# PESTAÑA 1: VENTAS (CORREGIDA DEFINITIVA)
# =======================================================
class TabVenta(QWidget):
    def __init__(self): 
        super().__init__()
        self.usuario = "Anon"
        self.carrito = []
        self.initUI()

    def set_usuario(self, u): self.usuario = u
    
    def initUI(self):
        l = QHBoxLayout(self)
        izq = QVBoxLayout()
        
        self.inp = QLineEdit()
        self.inp.setPlaceholderText("🔍 Buscar (Enter)")
        self.inp.returnPressed.connect(self.buscar)
        
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(6)
        self.tbl.setHorizontalHeaderLabels(["Producto","Precio","Cant","Dto%","Subtotal","X"])
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl.setSelectionMode(QTableWidget.SingleSelection)
        
        izq.addWidget(QLabel("<h3>Caja</h3>"))
        izq.addWidget(self.inp)
        izq.addWidget(self.tbl)
        
        der = QVBoxLayout()
        # AQUÍ DEFINIMOS EL NOMBRE CORRECTO: self.lbl_tot
        self.lbl_tot = QLabel("$0") 
        self.lbl_tot.setAlignment(Qt.AlignCenter)
        self.lbl_tot.setStyleSheet("font-size:45px;color:#2E7D32;font-weight:bold")
        
        bs = "padding:15px;color:white;font-weight:bold;border-radius:5px"
        bd = QPushButton("🏷️ Descuento"); bd.setStyleSheet(f"background:#FBC02D;{bs}"); bd.clicked.connect(self.dcto)
        b1 = QPushButton("💵 Efectivo (F1)"); b1.setStyleSheet(f"background:#2E7D32;{bs}"); b1.clicked.connect(lambda:self.cobrar("Efectivo"))
        b2 = QPushButton("💳 Tarjeta (F2)"); b2.setStyleSheet(f"background:#1565C0;{bs}"); b2.clicked.connect(lambda:self.cobrar("Tarjeta"))
        b3 = QPushButton("📱 Transf (F3)"); b3.setStyleSheet(f"background:#6A1B9A;{bs}"); b3.clicked.connect(self.trans)
        b4 = QPushButton("❌ Cancelar"); b4.setStyleSheet(f"background:#C62828;{bs}"); b4.clicked.connect(self.cls)
        
        QShortcut(QKeySequence("F1"),self).activated.connect(lambda:self.cobrar("Efectivo"))
        QShortcut(QKeySequence("F2"),self).activated.connect(lambda:self.cobrar("Tarjeta"))
        QShortcut(QKeySequence("F3"),self).activated.connect(self.trans)
        
        der.addWidget(QLabel("TOTAL:"))
        der.addWidget(self.lbl_tot)
        der.addSpacing(10)
        der.addWidget(bd)
        der.addWidget(b1)
        der.addWidget(b2)
        der.addWidget(b3)
        der.addStretch()
        der.addWidget(b4)
        
        l.addLayout(izq, 65)
        l.addLayout(der, 35)

    def buscar(self):
        t = self.inp.text().strip()
        if not t: return
        try:
            conn = pymysql.connect(**DB_CONFIG)
            c = conn.cursor()
            c.execute("SELECT sku,nombre,precio,tipo_venta,stock FROM productos WHERE sku=%s OR nombre LIKE %s LIMIT 20", (t, f"%{t}%"))
            res = c.fetchall()
            conn.close()
            
            if len(res) == 0: QMessageBox.warning(self,"Ups","No encontrado")
            elif len(res) == 1: self.add(res[0]); self.inp.clear()
            else:
                sel = SelectorProductoDialog(res)
                if sel.exec_() == QDialog.Accepted and sel.sel: 
                    self.add(sel.sel)
                    self.inp.clear()
        except: pass

    def add(self, p):
        sku, nom, pr, tip = p[0], p[1], float(p[2]), p[3]
        cant = 1.0
        if "granel" in str(tip).lower():
            v, ok = QInputDialog.getDouble(self, "Peso", f"{nom}\nKilos:", 0.5, 0, 100, 3)
            if ok: cant = v
            else: return
        
        found = False
        if "unidad" in str(tip).lower():
            for it in self.carrito:
                if it['sku'] == sku:
                    it['cant'] += 1
                    it['sub'] = it['cant'] * it['pr'] * (1 - it.get('descuento',0))
                    found = True
                    break
        
        if not found: 
            self.carrito.append({"sku":sku, "nom":nom, "pr":pr, "cant":cant, "sub":pr*cant, "tipo":tip, "descuento":0.0})
        self.render()

    def dcto(self):
        r = self.tbl.currentRow()
        if r < 0: return
        it = self.carrito[r]
        v, ok = QInputDialog.getInt(self, "Descuento", f"% Descuento para {it['nom']}:", 10, 0, 100, 5)
        if ok:
            it['descuento'] = v / 100.0
            it['sub'] = it['cant'] * it['pr'] * (1 - it['descuento'])
            self.render()

    def render(self):
        self.tbl.setRowCount(0)
        tot = 0
        for i, it in enumerate(self.carrito):
            self.tbl.insertRow(i)
            self.tbl.setItem(i, 0, QTableWidgetItem(it['nom']))
            self.tbl.setItem(i, 1, QTableWidgetItem(f"${it['pr']:,.0f}"))
            
            fmt = f"{it['cant']:.3f}" if "granel" in str(it['tipo']).lower() else f"{int(it['cant'])}"
            self.tbl.setItem(i, 2, QTableWidgetItem(fmt))
            
            d = f"{int(it.get('descuento',0)*100)}%" if it.get('descuento',0) > 0 else "-"
            self.tbl.setItem(i, 3, QTableWidgetItem(d))
            
            self.tbl.setItem(i, 4, QTableWidgetItem(f"${it['sub']:,.0f}"))
            
            b = QPushButton("X")
            b.setStyleSheet("color:red;font-weight:bold;border:none")
            b.clicked.connect(lambda _,x=i:self.dele(x))
            self.tbl.setCellWidget(i, 5, b)
            
            tot += it['sub']
        # CORRECCIÓN: Usamos self.lbl_tot consistentemente
        self.lbl_tot.setText(f"${tot:,.0f}".replace(",", "."))

    def dele(self, i): self.carrito.pop(i); self.render()
    def cls(self): self.carrito=[]; self.render(); self.inp.setFocus()
    def trans(self):
        id, ok = QInputDialog.getText(self, "ID", "ID Comprobante:")
        if ok and id: self.cobrar(f"Transf (ID: {id})")

    def cobrar(self, met):
        if not self.carrito: return
        if QMessageBox.question(self, "Cobrar", f"{met}\n¿Procesar?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.No: return
        try:
            conn = pymysql.connect(**DB_CONFIG)
            c = conn.cursor()
            idv = datetime.now().strftime("%Y%m%d-%H%M%S")
            
            # CORRECCIÓN: Usamos self.lbl_tot
            tot = float(self.lbl_tot.text().replace("$","").replace(".",""))
            
            # CORRECCIÓN SQL: Usamos nombres explícitos 'usuario' y 'venta_id'
            c.execute("INSERT INTO ventas (id, fecha, total, metodo_pago, usuario) VALUES (%s, NOW(), %s, %s, %s)", 
                      (idv, tot, met, self.usuario))
            
            for it in self.carrito:
                c.execute("INSERT INTO detalle_ventas (venta_id, producto_sku, cantidad, subtotal) VALUES (%s,%s,%s,%s)", 
                          (idv, it['sku'], it['cant'], it['sub']))
                
                c.execute("UPDATE productos SET stock=stock-%s WHERE sku=%s", (it['cant'], it['sku']))
            
            conn.commit()
            conn.close()
            
            generar_ticket_pdf(idv, self.carrito, tot, self.usuario, met)
            QMessageBox.information(self, "OK", "Venta Registrada")
            self.cls()
            
        except Exception as e: 
            QMessageBox.critical(self, "Error SQL", str(e))
# =======================================================
# PESTAÑA 2: INVENTARIO (VERSIÓN RELACIONAL CORREGIDA)
# =======================================================
class TabInventario(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # Barra superior
        panel_top = QHBoxLayout()
        self.filtro = QLineEdit()
        self.filtro.setPlaceholderText("🔍 Buscar por Nombre o SKU...")
        self.filtro.textChanged.connect(self.cargar_datos)
        
        btn_nuevo = QPushButton("➕ Nuevo")
        btn_nuevo.clicked.connect(self.nuevo_producto)
        
        btn_editar = QPushButton("✏️ Editar")
        btn_editar.clicked.connect(self.editar_producto)
        
        btn_stock = QPushButton("📦 Stock")
        btn_stock.setStyleSheet("background-color: #1976D2; color: white;")
        btn_stock.clicked.connect(self.sumar_stock)
        
        btn_borrar = QPushButton("🗑️ Borrar")
        btn_borrar.setStyleSheet("background-color: #C62828; color: white;")
        btn_borrar.clicked.connect(self.borrar_producto)
        
        btn_refresh = QPushButton("🔄")
        btn_refresh.clicked.connect(self.cargar_datos)
        
        panel_top.addWidget(self.filtro)
        panel_top.addWidget(btn_nuevo)
        panel_top.addWidget(btn_editar)
        panel_top.addWidget(btn_stock)
        panel_top.addWidget(btn_borrar)
        panel_top.addWidget(btn_refresh)
        
        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["SKU", "Nombre", "Costo", "Venta", "Stock", "Categoría"])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        
        layout.addLayout(panel_top)
        layout.addWidget(self.tabla)
        
        self.cargar_datos()

    def cargar_datos(self):
        texto = self.filtro.text().strip()
        try:
            self.tabla.blockSignals(True)
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # --- CONSULTA RELACIONAL SEGURA ---
            # Usamos IFNULL(c.nombre, 'General') para que no falle si el producto no tiene categoría
            sql = """
                SELECT p.sku, p.nombre, p.costo, p.precio, p.stock, IFNULL(c.nombre, 'General') 
                FROM productos p 
                LEFT JOIN categorias c ON p.categoria_id = c.id
            """
            
            if texto:
                sql += f" WHERE p.nombre LIKE '%{texto}%' OR p.sku LIKE '%{texto}%'"
            
            
            cursor.execute(sql)
            datos = cursor.fetchall()
            conn.close()

            self.tabla.setRowCount(0)
            for i, fila in enumerate(datos):
                self.tabla.insertRow(i)
                # SKU
                item_sku = QTableWidgetItem(str(fila[0]))
                item_sku.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.tabla.setItem(i, 0, item_sku)
                
                # Nombre, Costo, Precio, Stock, Categoria
                self.tabla.setItem(i, 1, QTableWidgetItem(str(fila[1])))
                self.tabla.setItem(i, 2, QTableWidgetItem(f"{float(fila[2]):.0f}")) # Costo sin decimales visuales
                self.tabla.setItem(i, 3, QTableWidgetItem(f"{float(fila[3]):.0f}")) # Precio sin decimales visuales
                self.tabla.setItem(i, 4, QTableWidgetItem(str(fila[4])))
                self.tabla.setItem(i, 5, QTableWidgetItem(str(fila[5])))
            
            self.tabla.blockSignals(False)
            
        except Exception as e:
            print(f"❌ ERROR CARGANDO INVENTARIO: {e}") # ¡MIRA LA TERMINAL SI FALLA!
            self.tabla.blockSignals(False)

    # --- FUNCIONES DE GESTIÓN ---
    def nuevo_producto(self):
        d = QDialog(self); l = QFormLayout(d); d.setWindowTitle("Nuevo Producto")
        sku, nom, cst, prc, cat = QLineEdit(), QLineEdit(), QLineEdit("0"), QLineEdit("0"), QLineEdit("General")
        tipo = QComboBox(); tipo.addItems(["Unidad", "Granel"])
        btn = QPushButton("Guardar")
        
        l.addRow("SKU:", sku); l.addRow("Nombre:", nom); l.addRow("Costo:", cst)
        l.addRow("Precio:", prc); l.addRow("Categoría:", cat); l.addRow("Tipo:", tipo); l.addRow(btn)
        
        def guardar():
            try:
                conn = pymysql.connect(**DB_CONFIG); c = conn.cursor()
                # Lógica para buscar/crear categoría (repite la lógica del importador)
                c.execute("SELECT id FROM categorias WHERE nombre=%s", (cat.text(),))
                res = c.fetchone()
                if res: cat_id = res[0]
                else:
                    c.execute("INSERT INTO categorias (nombre) VALUES (%s)", (cat.text(),))
                    cat_id = c.lastrowid
                
                c.execute("INSERT INTO productos (sku, nombre, costo, precio, categoria_id, tipo_venta, stock) VALUES (%s,%s,%s,%s,%s,%s,0)",
                          (sku.text(), nom.text(), float(cst.text()), float(prc.text()), cat_id, tipo.currentText()))
                conn.commit(); conn.close(); d.accept(); self.cargar_datos()
                QMessageBox.information(d, "OK", "Producto Creado")
            except Exception as e: QMessageBox.critical(d, "Error", str(e))
        
        btn.clicked.connect(guardar); d.exec_()

    def editar_producto(self):
        r = self.tabla.currentRow()
        if r < 0: return
        sku_orig = self.tabla.item(r, 0).text()
        
        d = QDialog(self); l = QFormLayout(d); d.setWindowTitle("Editar")
        # Leemos valores actuales de la tabla para rellenar
        nom = QLineEdit(self.tabla.item(r, 1).text())
        cst = QLineEdit(self.tabla.item(r, 2).text())
        prc = QLineEdit(self.tabla.item(r, 3).text())
        cat = QLineEdit(self.tabla.item(r, 5).text())
        btn = QPushButton("Actualizar")
        
        l.addRow("Nombre:", nom); l.addRow("Costo:", cst); l.addRow("Precio:", prc); l.addRow("Cat:", cat); l.addRow(btn)
        
        def guardar():
            try:
                conn = pymysql.connect(**DB_CONFIG); c = conn.cursor()
                # Gestión de Categoría
                c.execute("SELECT id FROM categorias WHERE nombre=%s", (cat.text(),))
                res = c.fetchone()
                if res: cat_id = res[0]
                else:
                    c.execute("INSERT INTO categorias (nombre) VALUES (%s)", (cat.text(),))
                    cat_id = c.lastrowid
                
                c.execute("UPDATE productos SET nombre=%s, costo=%s, precio=%s, categoria_id=%s WHERE sku=%s",
                          (nom.text(), float(cst.text()), float(prc.text()), cat_id, sku_orig))
                conn.commit(); conn.close(); d.accept(); self.cargar_datos()
            except Exception as e: QMessageBox.critical(d, "Error", str(e))
        
        btn.clicked.connect(guardar); d.exec_()

    def sumar_stock(self):
        r = self.tabla.currentRow()
        if r < 0: return
        sku = self.tabla.item(r, 0).text()
        cant, ok = QInputDialog.getDouble(self, "Stock", "Cantidad a sumar:", 0, 0, 10000, 3)
        if ok:
            try:
                conn = pymysql.connect(**DB_CONFIG); c = conn.cursor()
                c.execute("UPDATE productos SET stock = stock + %s WHERE sku=%s", (cant, sku))
                conn.commit(); conn.close(); self.cargar_datos()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def borrar_producto(self):
        r = self.tabla.currentRow()
        if r < 0: return
        sku = self.tabla.item(r, 0).text()
        if QMessageBox.question(self, "Borrar", "¿Seguro?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            try:
                conn = pymysql.connect(**DB_CONFIG); c = conn.cursor()
                c.execute("DELETE FROM productos WHERE sku=%s", (sku,))
                conn.commit(); conn.close(); self.cargar_datos()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

# =======================================================
# PESTAÑA 3: GASTOS
# =======================================================
class TabGastos(QWidget):
    def __init__(self): super().__init__(); self.initUI()
    def initUI(self):
        l = QHBoxLayout(self); f = QGroupBox("Nuevo"); fl = QFormLayout(f)
        con, mon, cat = QLineEdit(), QLineEdit(), QComboBox()
        cat.addItems(["Insumos","Mercadería","Servicios","Retiro/Sueldo","Otros"])
        b = QPushButton("Guardar"); b.clicked.connect(self.save)
        fl.addRow("Concepto", con); fl.addRow("Monto", mon); fl.addRow("Cat", cat); fl.addRow(b)
        
        self.t = QTableWidget(); self.t.setColumnCount(4); self.t.setHorizontalHeaderLabels(["Fecha","Concepto","Cat","Monto"])
        self.t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        l.addWidget(f, 35); l.addWidget(self.t, 65)
        self.con=con; self.mon=mon; self.cat=cat; self.load()
    
    def save(self):
        try:
            conn = pymysql.connect(**DB_CONFIG); c = conn.cursor()
            c.execute("INSERT INTO gastos (fecha,usuario,concepto,categoria,monto) VALUES (NOW(),'admin',%s,%s,%s)",
                      (self.con.text(), self.cat.currentText(), float(self.mon.text())))
            conn.commit(); conn.close(); self.load(); self.con.clear(); self.mon.clear()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))
    
    def load(self):
        try:
            conn = pymysql.connect(**DB_CONFIG); c = conn.cursor()
            c.execute("SELECT fecha,concepto,categoria,monto FROM gastos ORDER BY fecha DESC")
            d = c.fetchall(); conn.close(); self.t.setRowCount(0)
            for i,r in enumerate(d):
                self.t.insertRow(i)
                for j in range(4): self.t.setItem(i, j, QTableWidgetItem(str(r[j])))
        except: pass

# =======================================================
# PESTAÑA 4: CORTE (CORREGIDA SQL)
# =======================================================
class TabCorte(QWidget):
    def __init__(self, user): super().__init__(); self.user=user; self.msis=0; self.initUI()
    def initUI(self):
        l = QHBoxLayout(self)
        g = QGroupBox(f"Cierre: {self.user}"); f = QFormLayout(g)
        
        self.l_ef = QLabel("$0"); self.l_tj = QLabel("$0"); self.l_tr = QLabel("$0"); self.l_tot = QLabel("$0")
        self.l_tot.setStyleSheet("font-weight:bold;color:blue;font-size:16px")
        self.real = QLineEdit(); self.dif = QLabel("$0")
        
        b_ret = QPushButton("💸 Retiro Caja"); b_ret.clicked.connect(self.retiro)
        b_cls = QPushButton("🔒 Cerrar Turno"); b_cls.setStyleSheet("background:red;color:white"); b_cls.clicked.connect(self.close)
        b_cal = QPushButton("Calcular"); b_cal.clicked.connect(self.calc)

        f.addRow("Efectivo:", self.l_ef); f.addRow("Tarjeta:", self.l_tj); f.addRow("Transf:", self.l_tr)
        f.addRow("TOTAL:", self.l_tot)
        f.addRow(b_ret); f.addRow("Real:", self.real); f.addRow("Dif:", self.dif); f.addRow(b_cal); f.addRow(b_cls)
        
        der = QVBoxLayout(); self.tdet = QTableWidget(); self.tdet.setColumnCount(3)
        self.tdet.setHorizontalHeaderLabels(["Prod","Cant","Total"]); self.tdet.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        upd = QPushButton("Actualizar"); upd.clicked.connect(self.load)
        der.addWidget(QLabel("Detalle:")); der.addWidget(self.tdet); der.addWidget(upd)
        
        l.addWidget(g, 35); l.addLayout(der, 65); self.load()

    def load(self):
        try:
            conn = pymysql.connect(**DB_CONFIG); c = conn.cursor()
            # Totales
            c.execute("SELECT metodo_pago, SUM(total) FROM ventas WHERE DATE(fecha)=CURDATE() AND usuario=%s GROUP BY metodo_pago", (self.user,))
            res = c.fetchall(); ef=0; tj=0; tr=0; tot=0
            for r in res:
                m = r[0].lower(); v = float(r[1]); tot += v
                if "efec" in m: ef += v
                elif "tarj" in m: tj += v
                else: tr += v
            
            self.l_ef.setText(f"${ef:,.0f}"); self.l_tj.setText(f"${tj:,.0f}"); self.l_tr.setText(f"${tr:,.0f}"); self.l_tot.setText(f"${tot:,.0f}")
            self.msis = tot
            
            # Detalle (CORREGIDO: venta_id y producto_sku)
            sql = """SELECT p.nombre, SUM(dv.cantidad), SUM(dv.subtotal) 
                     FROM detalle_ventas dv 
                     JOIN ventas v ON dv.venta_id = v.id 
                     JOIN productos p ON dv.producto_sku = p.sku 
                     WHERE DATE(v.fecha)=CURDATE() AND v.usuario=%s 
                     GROUP BY p.nombre ORDER BY SUM(dv.subtotal) DESC"""
            c.execute(sql, (self.user,))
            d = c.fetchall(); self.tdet.setRowCount(0)
            for i, r in enumerate(d):
                self.tdet.insertRow(i)
                self.tdet.setItem(i, 0, QTableWidgetItem(str(r[0])))
                self.tdet.setItem(i, 1, QTableWidgetItem(f"{float(r[1]):.3f}"))
                self.tdet.setItem(i, 2, QTableWidgetItem(f"${float(r[2]):,.0f}"))
            conn.close()
        except: pass

    def retiro(self):
        v, ok = QInputDialog.getDouble(self, "Retiro", "Monto:", 0, 0, 1000000, 0)
        if ok:
            try:
                conn = pymysql.connect(**DB_CONFIG); c = conn.cursor()
                c.execute("INSERT INTO gastos (fecha,usuario,concepto,categoria,monto) VALUES (NOW(),%s,'Retiro Caja','Retiro',%s)", (self.user, v))
                conn.commit(); conn.close(); QMessageBox.information(self, "OK", "Registrado")
            except: pass

    def calc(self):
        try:
            r = float(self.real.text()); d = r - self.msis; self.dif.setText(f"${d:,.0f}")
        except: pass

    def close(self):
        self.calc()
        if QMessageBox.question(self, "Cerrar", "Seguro?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.No: return
        try:
            r = float(self.real.text())
            conn = pymysql.connect(**DB_CONFIG); c = conn.cursor()
            c.execute("INSERT INTO corte_caja (fecha,usuario,ventas_sistema,dinero_real,diferencia) VALUES (NOW(),%s,%s,%s,%s)",
                      (self.user, self.msis, r, r-self.msis))
            conn.commit(); conn.close()
            QMessageBox.information(self, "OK", "Guardado"); self.tdet.setRowCount(0); self.l_tot.setText("$0")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))
# =======================================================
# PESTAÑA 5: REPORTES (CORREGIDA SQL)
# =======================================================
class TabReportes(QWidget):
    def __init__(self): super().__init__(); self.initUI()
    def initUI(self):
        l = QVBoxLayout(self)
        top = QHBoxLayout()
        self.dt = QDateEdit(); self.dt.setDate(QDate.currentDate()); self.dt.setCalendarPopup(True)
        self.cb = QComboBox(); self.cb.addItems(["Día (Hora)", "Semana (Día)"])
        btn = QPushButton("Generar"); btn.clicked.connect(self.gen)
        top.addWidget(QLabel("Fecha:")); top.addWidget(self.dt); top.addWidget(self.cb); top.addWidget(btn); top.addStretch()
        
        self.fig = Figure(); self.can = FigureCanvas(self.fig); self.lbl = QLabel("...")
        l.addLayout(top); l.addWidget(self.can); l.addWidget(self.lbl)

    def gen(self):
        f = self.dt.date().toString("yyyy-MM-dd"); idx = self.cb.currentIndex()
        try:
            conn = pymysql.connect(**DB_CONFIG); c = conn.cursor()
            sql = ""
            
            # CORRECCIÓN AQUÍ: venta_id y producto_sku
            if idx == 0: # Dia
                sql = """SELECT HOUR(v.fecha), SUM(dv.subtotal-(IFNULL(p.costo,0)*dv.cantidad)) 
                         FROM ventas v 
                         JOIN detalle_ventas dv ON v.id = dv.venta_id 
                         JOIN productos p ON dv.producto_sku = p.sku 
                         WHERE DATE(v.fecha)=%s 
                         GROUP BY HOUR(v.fecha) ORDER BY HOUR(v.fecha)"""
            else: # Semana
                sql = """SELECT WEEKDAY(v.fecha), SUM(dv.subtotal-(IFNULL(p.costo,0)*dv.cantidad)) 
                         FROM ventas v 
                         JOIN detalle_ventas dv ON v.id = dv.venta_id 
                         JOIN productos p ON dv.producto_sku = p.sku 
                         WHERE YEARWEEK(v.fecha,1)=YEARWEEK(%s,1) 
                         GROUP BY WEEKDAY(v.fecha)"""
            
            c.execute(sql, (f,)); data = c.fetchall(); conn.close()
            
            self.fig.clear(); ax = self.fig.add_subplot(111)
            x, y, tot = [], [], 0
            dias = ["Lu","Ma","Mi","Ju","Vi","Sa","Do"]
            
            if not data:
                self.lbl.setText("No hay datos para este período")
                self.can.draw()
                return

            for r in data:
                lbl = f"{r[0]}:00" if idx == 0 else dias[r[0]]
                val = float(r[1]); x.append(lbl); y.append(val); tot += val
            
            ax.bar(x, y, color='orange'); ax.set_title("Margen de Ganancia ($)"); self.can.draw()
            self.lbl.setText(f"Margen Total: <b>${tot:,.0f}</b>")
            
        except Exception as e: QMessageBox.critical(self, "Error", str(e))              
# =======================================================
# MAIN
# =======================================================
class SistemaFinal(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.setWindowTitle(f"Mercadito 'O' - {user}")
        self.setGeometry(50, 50, 1200, 750)
        QApplication.setStyle("Fusion")
        
        w = QWidget(); self.setCentralWidget(w); l = QVBoxLayout(w)
        top = QHBoxLayout(); top.addWidget(QLabel(f"👤 {user}")); btn = QPushButton("Cerrar Sesión"); btn.clicked.connect(self.close)
        top.addStretch(); top.addWidget(btn)
        
        tabs = QTabWidget()
        tabs.addTab(TabVenta(), "🛒 Caja"); tabs.widget(0).set_usuario(user)
        tabs.addTab(TabInventario(), "📦 Inventario")
        tabs.addTab(TabGastos(), "💸 Gastos")
        tabs.addTab(TabCorte(user), "💰 Corte")
        tabs.addTab(TabReportes(), "📊 Reportes")
        
        l.addLayout(top); l.addWidget(tabs)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    while True:
        l = LoginDialog()
        if l.exec_() == QDialog.Accepted:
            w = SistemaFinal(l.usuario_logueado)
            w.show(); app.exec_()
        else: break
    sys.exit()