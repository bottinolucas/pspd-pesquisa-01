CREATE SCHEMA IF NOT EXISTS catalogo;

CREATE TABLE IF NOT EXISTS catalogo.livros (
    isbn    VARCHAR(30) PRIMARY KEY,
    titulo  TEXT        NOT NULL,
    autor   TEXT        NOT NULL,
    ano     INTEGER     NOT NULL
);

INSERT INTO catalogo.livros (isbn, titulo, autor, ano) VALUES
  ('978-0-13-468599-1', 'Clean Code',                            'Robert C. Martin', 2008),
  ('978-0-201-63361-0', 'Design Patterns',                       'Gang of Four',     1994),
  ('978-0-13-235088-4', 'The Pragmatic Programmer',              'Thomas & Hunt',    1999),
  ('978-1-491-95039-9', 'Designing Data-Intensive Applications', 'Martin Kleppmann', 2017),
  ('978-0-596-51774-8', 'Programming Python',                    'Mark Lutz',        2011)
ON CONFLICT DO NOTHING;
