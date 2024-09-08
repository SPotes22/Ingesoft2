use bwpeie9ps3tadhnabxac;

CREATE TABLE if not exists users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_usuario_plataforma VARCHAR(255),
    nombre_plataforma VARCHAR(255)
);

CREATE TABLE empleado (
    Codigo_empleado INT PRIMARY KEY,  -- Clave principal
    Id INT,  -- Clave foránea
    rol VARCHAR(50),
    salario DECIMAL(10, 2),
    pension DECIMAL(10, 2),
    arl VARCHAR(250),
    sem_acum INT,
    psico VARCHAR(3),
    fisico VARCHAR(3),
    indux VARCHAR(3),
    nota DECIMAL(3, 2),
    FOREIGN KEY (Id) REFERENCES users(Id)  -- Ajusta "otra_tabla" con el nombre de la tabla relacionada
);