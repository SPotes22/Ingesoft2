from flask import Flask, render_template , request , redirect , url_for
import os
import database as db

template_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
template_dir = os.path.join(template_dir,"src","templates")

app = Flask(__name__, template_folder = template_dir)

# rutas de la aplicacion

@app.route('/')
def home():
    cursor = db.database.cursor()
    
    # Obtener usuarios
    cursor.execute("SELECT * FROM usuarios")
    myresult = cursor.fetchall()
    insertObject = []
    columNames = [column[0] for column in cursor.description]
    for record in myresult:
        insertObject.append(dict(zip(columNames, record)))

    # Obtener roles
    cursor.execute("SELECT * FROM roles")
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