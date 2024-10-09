from flask import Flask, render_template , request , redirect , url_for , session
import os
import database as db
from datetime import date

template_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
template_dir = os.path.join(template_dir,"src","templates")

app = Flask(__name__, template_folder = template_dir)
app.secret_key = 'mi_clave_super_secreta_123'

# rutas de la aplicacion

@app.route('/')
def home():
    cursor = db.database.cursor()
    
    # Obtener usuarios
    cursor.execute("SELECT * FROM usuarios")
    myresult = cursor.fetchall()  # Asegúrate de que los resultados son leídos completamente
    insertObject = []
    columNames = [column[0] for column in cursor.description]
    for record in myresult:
        insertObject.append(dict(zip(columNames, record)))

    # Obtener roles
    cursor.execute("SELECT * FROM roles")  # Aquí no debería haber conflictos si la consulta anterior fue leída completamente
    roles = cursor.fetchall()
    roles_list = [{"id": role[0], "nombre": role[1]} for role in roles]  # Convertir a lista de diccionarios

    cursor.close()
    
    return render_template("index.html", data=insertObject, roles=roles_list)  # Pasar roles a la plantilla


#ruta para guardar usuarios en bd
@app.route('/user', methods=["POST"])
def addUser():
    username = request.form['nombre']
    email = request.form['email']
    password = request.form['password']
    rol_id = request.form['rol']  # Obtener el rol del formulario
    
    if username and email and password and rol_id: 
        cursor = db.database.cursor()
        sql = "INSERT INTO usuarios (nombre, email, password, rol_id) VALUES (%s, %s, %s, %s)"
        data = (username, email, password, rol_id)
        cursor.execute(sql, data)
        db.database.commit()
        cursor.close()
    return redirect(url_for('home'))


@app.route('/delete/<string:id>')
def delete(id):
    cursor = db.database.cursor()
    sql = "DELETE FROM usuarios WHERE id = %s"
    data = (id,)
    cursor.execute(sql,data)
    db.database.commit()
    return redirect(url_for('home'))

@app.route('/edit/<string:id>', methods=["POST"])
def edit(id):
    username = request.form['nombre']
    email = request.form['email']
    password = request.form['password']
    rol_id = request.form['rol']

    print(f"Actualizando usuario ID: {id}, Nombre: {username}, Email: {email}, Rol: {rol_id}")  # Para verificar

    if username and email and password and rol_id:
        cursor = db.database.cursor()
        sql = "UPDATE usuarios SET nombre = %s, email = %s, password = %s, rol_id = %s WHERE id = %s"
        data = (username, email, password, rol_id, id)
        cursor.execute(sql, data)
        db.database.commit()
        cursor.close()

    return redirect(url_for('home'))

@app.route('/bonos', methods=["GET"])
def bonos():
    # Verificar si el usuario está logueado
    if not is_logged_in():
        return redirect(url_for('login'))
    
    # Verificar si el usuario tiene el rol de HR
    if current_user_rol() != 'HR':
        return render_template("error.html", mensaje="Rol incorrecto para acceder a este portal")

    cursor = db.database.cursor()

    # Obtener la lista de usuarios para mostrar en la página de bonos
    query = """
    SELECT u.id, u.nombre, u.email 
    FROM usuarios u
    """
    cursor.execute(query)
    usuarios = cursor.fetchall()

    cursor.close()

    return render_template('bonos.html', usuarios=usuarios)


@app.route('/añadir_bonificacion', methods=['POST'])
def añadir_bonificacion():
    usuario_id = request.form['usuario_id']
    monto = request.form['monto']
    descripcion = request.form['descripcion']
    fecha_asignacion = request.form['fecha_asignacion']

    cursor = db.database.cursor()
    query = "INSERT INTO bonos (usuario_id, monto, descripcion, fecha_asignacion) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (usuario_id, monto, descripcion, fecha_asignacion))
    db.database.commit()

    cursor.close()
    return redirect(url_for('bonos'))

@app.route('/insertar_horas', methods=['POST'])
def insertar_horas():
    usuario_id = request.form['usuario_id']
    horas_normales = request.form['horas_normales']
    horas_extras = request.form['horas_extras']
    horas_festivas = request.form['horas_festivas']

    cursor = db.database.cursor()
    query = "INSERT INTO horas_trabajadas (usuario_id, horas_normales, horas_extras, horas_extra_diurna_festiva) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (usuario_id, horas_normales, horas_extras, horas_festivas))
    db.database.commit()

    cursor.close()
    return redirect(url_for('bonos'))

def current_user_rol():
    # Verifica si el usuario está autenticado y tiene un rol asociado en la sesión
    if 'user_id' in session:
        cursor = db.database.cursor()

        # Se cambia la consulta para obtener el nombre del rol desde la tabla `roles`
        query = """
        SELECT r.nombre 
        FROM usuarios u 
        JOIN roles r ON u.rol_id = r.id 
        WHERE u.id = %s
        """
        cursor.execute(query, (session['user_id'],))
        result = cursor.fetchone()

        cursor.close()

        if result:
            return result[0]  # Retorna el nombre del rol del usuario
    return None  # Si no hay usuario logueado o no tiene rol


@app.route('/pruebas', methods=["GET"])
def pruebas():
    cursor = db.database.cursor()

    # Filtrar usuarios con rol 'Usuario' y obtener detalles de la tabla 'contrataciones'
    query = """
    SELECT u.id, u.nombre, u.email, u.password, r.nombre as rol, 
           c.rol_asignado, c.salario, c.fecha_contratacion, c.resultados_pruebas 
    FROM usuarios u
    INNER JOIN roles r ON u.rol_id = r.id
    LEFT JOIN contrataciones c ON u.id = c.usuario_id
    WHERE r.nombre = 'User'
    """
    cursor.execute(query)
    usuarios = cursor.fetchall()

    # Convertir los datos a diccionario
    usuarios_data = []
    columNames = [column[0] for column in cursor.description]
    for usuario in usuarios:
        usuarios_data.append(dict(zip(columNames, usuario)))

    cursor.close()
    return render_template("pruebas.html", usuarios=usuarios_data)

@app.route('/update_contract/<int:usuario_id>', methods=["POST"])
def update_contract(usuario_id):
    rol_asignado = request.form['rol_asignado']
    salario = request.form['salario']
    fecha_contratacion = request.form['fecha_contratacion']
    resultados_pruebas = request.form['resultados_pruebas']

    cursor = db.database.cursor()

    # Verificamos si ya existe una contratación para este usuario
    query_check = "SELECT id FROM contrataciones WHERE usuario_id = %s"
    cursor.execute(query_check, (usuario_id,))
    contratacion = cursor.fetchone()

    if contratacion:
        # Actualizar la fila existente
        query_update = """
        UPDATE contrataciones
        SET rol_asignado = %s, salario = %s, fecha_contratacion = %s, resultados_pruebas = %s
        WHERE usuario_id = %s
        """
        cursor.execute(query_update, (rol_asignado, salario, fecha_contratacion, resultados_pruebas, usuario_id))
    else:
        # Insertar nueva fila si no existe
        query_insert = """
        INSERT INTO contrataciones (usuario_id, rol_asignado, salario, fecha_contratacion, resultados_pruebas)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query_insert, (usuario_id, rol_asignado, salario, fecha_contratacion, resultados_pruebas))

    db.database.commit()
    cursor.close()

    return redirect(url_for('pruebas'))


# Autenticación ficticia
def is_logged_in():
    return 'user_id' in session

@app.route('/nomina', methods=['GET', 'POST'])
def nomina():
    if not is_logged_in():
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = db.database.cursor()

    try:
        # Obtener información del usuario y sus horas trabajadas
        query = """
        SELECT u.nombre, u.email, c.salario, h.horas_normales, h.horas_extras, h.horas_extra_diurna_festiva
        FROM usuarios u
        JOIN contrataciones c ON u.id = c.usuario_id
        LEFT JOIN horas_trabajadas h ON u.id = h.usuario_id
        WHERE u.id = %s
        GROUP BY u.id, u.nombre, u.email, c.salario, h.horas_normales, h.horas_extras, h.horas_extra_diurna_festiva
        """
        cursor.execute(query, (user_id,))
        usuario = cursor.fetchone()

        # Verificar si hay datos del usuario
        if not usuario:
            return "Usuario no encontrado", 404

        if request.method == "POST":
            # Obtener las horas ingresadas en el formulario
            horas_trab = float(request.form['horas_trab'])
            hora_extra = float(request.form['hora_extra'])
            hora_extra_festiva = float(request.form['hora_extra_festiva'])

            # Insertar o actualizar las horas trabajadas
            if usuario[3] is None:  # Si el usuario no tiene horas registradas
                query_insert = """
                INSERT INTO horas_trabajadas (usuario_id, horas_normales, horas_extras, horas_extra_diurna_festiva)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query_insert, (user_id, horas_trab, hora_extra, hora_extra_festiva))
            else:
                query_update = """
                UPDATE horas_trabajadas
                SET horas_normales = %s, horas_extras = %s, horas_extra_diurna_festiva = %s
                WHERE usuario_id = %s
                """
                cursor.execute(query_update, (horas_trab, hora_extra, hora_extra_festiva, user_id))

            db.database.commit()

            # Calcular nómina
            salario_base = float(usuario[2])
            total_nomina = ((salario_base / 208) * horas_trab) + (hora_extra * 7065) + (hora_extra_festiva * 11304)
            deducciones = salario_base * 0.08
            total_nomina -= deducciones

            # Renderizar la nómina calculada
            return render_template("nomina.html", usuario=usuario, ingresar_horas=False, nomina=total_nomina)

        # Si es GET, renderizar el formulario si no hay horas ingresadas
        if usuario[3] is None:
            return render_template("nomina.html", usuario=usuario, ingresar_horas=True)

        # Si ya tiene horas registradas, calcular la nómina y mostrarla
        salario_base = float(usuario[2])
        horas_trabajadas = float(usuario[3])
        hora_extra = float(usuario[4])
        hora_extra_festiva = float(usuario[5])

        total_nomina = ((salario_base / 208) * horas_trabajadas) + (hora_extra * 7065) + (hora_extra_festiva * 11304)
        deducciones = salario_base * 0.08
        total_nomina -= deducciones

        return render_template("nomina.html", usuario=usuario, ingresar_horas=False, nomina=total_nomina)
    
    finally:
        cursor.close()


@app.route('/liquidacion', methods=['GET'])
def liquidacion():
    if not is_logged_in():
        return redirect(url_for('login'))

    cursor = db.database.cursor()

    try:
        # Consulta para obtener los usuarios que tienen horas registradas
        query = """
        SELECT u.id, u.nombre, u.email, c.salario, SUM(h.horas_normales) AS horas_normales, SUM(h.horas_extras) AS horas_extras, SUM(h.horas_extra_diurna_festiva) AS horas_extra_diurna_festiva
        FROM usuarios u
        JOIN contrataciones c ON u.id = c.usuario_id
        LEFT JOIN horas_trabajadas h ON u.id = h.usuario_id
        WHERE h.horas_normales IS NOT NULL
        GROUP BY u.id, u.nombre, u.email, c.salario;

        """
        cursor.execute(query)
        usuarios = cursor.fetchall()

        return render_template("liquidacion.html", usuarios=usuarios)

    finally:
        cursor.close()

@app.route('/eliminar_usuario', methods=['POST'])
def eliminar_usuario():
    if not is_logged_in():
        return redirect(url_for('login'))

    usuario_id = request.form['usuario_id']

    cursor = db.database.cursor()

    # Eliminar al usuario de las tablas correspondientes
    query_horas = "DELETE FROM horas_trabajadas WHERE usuario_id = %s"
    cursor.execute(query_horas, (usuario_id,))

    query_contrataciones = "DELETE FROM contrataciones WHERE usuario_id = %s"
    cursor.execute(query_contrataciones, (usuario_id,))

    query_usuario = "DELETE FROM usuarios WHERE id = %s"
    cursor.execute(query_usuario, (usuario_id,))

    db.database.commit()
    cursor.close()

    return redirect(url_for('liquidacion'))

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        
        # Verifica las credenciales del usuario
        cursor = db.database.cursor()
        query = "SELECT id FROM usuarios WHERE nombre = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        
        if user:
            session['user_id'] = user[0]  # Guarda el ID del usuario en la sesión
            return redirect(url_for('nomina'))  # Redirige a la página de nómina
        else:
            return "Credenciales incorrectas"
    
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()  # Elimina toda la información de la sesión
    return redirect(url_for('login'))  # Redirige al usuario a la página de inicio de sesión

@app.route('/create/')
def create():
    # este endpoint es utilizado para generar la estructura de la base de datos que utiliza la aplicacion,
    # pudiendo cambiar de base de datos más fácilmente
    cursor = db.database.cursor()
    
    # Lista de sentencias SQL individuales
    sql_statements = [
        """
        CREATE TABLE roles (
            id INT PRIMARY KEY AUTO_INCREMENT,
            nombre VARCHAR(50) NOT NULL UNIQUE
        )
        """,
        """
        CREATE TABLE usuarios (
            id INT PRIMARY KEY AUTO_INCREMENT,
            nombre VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            rol_id INT,
            FOREIGN KEY (rol_id) REFERENCES roles(id)
        )
        """,
        """
        CREATE TABLE contrataciones (
            id INT PRIMARY KEY AUTO_INCREMENT,
            usuario_id INT NOT NULL,
            rol_asignado VARCHAR(50) NOT NULL,
            salario DECIMAL(10, 2) NOT NULL,
            fecha_contratacion DATE NOT NULL,
            resultados_pruebas TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
        """,
        """
        CREATE TABLE horas_trabajadas (
            id INT PRIMARY KEY AUTO_INCREMENT,
            usuario_id INT NOT NULL,
            horas_normales DECIMAL(5, 2) DEFAULT 0.00,
            horas_extras DECIMAL(5, 2) DEFAULT 0.00,
            horas_extra_diurna_festiva DECIMAL(5, 2) DEFAULT 0.00,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
        """,
        """
        CREATE TABLE bonos (
            id INT PRIMARY KEY AUTO_INCREMENT,
            usuario_id INT NOT NULL,
            monto DECIMAL(10, 2) NOT NULL,
            descripcion TEXT,
            fecha_asignacion DATE NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
        """,
        """
        INSERT INTO roles (nombre) VALUES ('Admin'), ('HR'), ('Usuario');
        """,
        """
        INSERT INTO usuarios (nombre, email, password, rol_id) 
        VALUES ('Admin1', 'admin1@correo.com', 'password_hash', (SELECT id FROM roles WHERE nombre = 'Admin'));
        """,
        """
        INSERT INTO usuarios (nombre, email, password, rol_id) 
        VALUES ('HR1', 'hr1@correo.com', 'password_hash', (SELECT id FROM roles WHERE nombre = 'HR'));
        """
    ]

    # Ejecuta cada sentencia SQL individualmente
    for sql in sql_statements:
        cursor.execute(sql)

    db.database.commit()
    cursor.close()

    return redirect(url_for('home'))

@app.route('/assing/')
def assing():
    cursor = db.database.cursor()
    
    # Lista de sentencias SQL individuales
    sql_statements = [
        """
        INSERT INTO roles (nombre) VALUES ('User');
        """,
    ]

    # Ejecuta cada sentencia SQL individualmente
    for sql in sql_statements:
        cursor.execute(sql)

    db.database.commit()
    cursor.close()

    return redirect(url_for('home'))
    
    

if __name__ == '__main__':
    app.run(debug=True, port=4000)