# 🏢 Multi-tenancy jerárquico — modelo y RLS

> Cómo la plataforma **aísla los datos de cada cliente** sobre schemas compartidos, con un **árbol de tenants**
> y **una sola política de RLS por subárbol**. Doc de arquitectura (descriptivo: *cómo y por qué*).
> Las decisiones y su contexto viven en [`gobernanza-db.md`](./gobernanza-db.md).

## Idea central

Los tenants forman un **árbol**: la **plataforma** (raíz) → **clientes** → **sub-unidades/sucursales** (hijos).
La regla de visibilidad es **una sola**:

> **Cada quien ve su subárbol** (él mismo + sus descendientes).

| Quién | Posición en el árbol | Ve |
|---|---|---|
| Plataforma (los desarrolladores) | raíz | **todo** (todos son sus descendientes) |
| Cliente (Tienda A, matriz) | nodo | A + sus sucursales |
| Sucursal (A-Norte) | hoja | solo A-Norte |

El multi-tenancy **plano** es un caso particular: un árbol de 2 niveles (raíz + clientes). Por eso esta política los cubre a los dos.

## Piezas

1. **Tabla `app.tenants`** — el árbol: `id (uuid)`, `parent_id`, `path (ltree)`, `name`, `type`.
   Es **estado/referencia** → **bitemporal** (permite reconstruir "quién fue hijo de quién y cuándo").
2. **Contexto de sesión** — la app, tras autenticar al usuario, fija por request: `SET LOCAL app.current_tenant = '<uuid>'`.
3. **Función `admin.subtree(tenant)`** — devuelve el tenant y todos sus descendientes (vía `ltree`, rápido e indexado con GiST).
4. **Política RLS única** (en `app` y `gold`):
   ```sql
   USING (tenant_id <@ (SELECT path FROM app.tenants
                        WHERE id = current_setting('app.current_tenant')::uuid))
   -- o equivalente: tenant_id IN (SELECT id FROM admin.subtree(current_setting('app.current_tenant')::uuid))
   ```

## Ejemplo

```
plataforma
├── tienda_a
│   ├── a_norte
│   └── a_sur
└── tienda_b
```

- **María** (sesión = `a_norte`) → ve **solo `a_norte`**.
- **Gerente de Tienda A** (sesión = `tienda_a`) → ve **`a` + `a_norte` + `a_sur`**.
- **La plataforma** (sesión = `plataforma`, raíz) → ve **todo**.
- **Un externo de Tienda B** (tras la API, sesión = `tienda_b`) → ve **solo `b`**.

## Rol ≠ alcance (son ortogonales)

- El **rol** (`app_user`, `read_external`, `read_internal`, …) define la **capacidad** (CRUD vs lectura) y la **vía** (directo vs API).
- La **posición en el árbol** (el `current_tenant` de la sesión) define el **alcance** (qué subárbol).
- `read_external` (tras API) y `read_internal` (directo) **se mantienen separados por vía de acceso**: el RLS es el
  mismo, pero la vía **retroalimenta** la gobernanza (auditoría y scoping distintos).
- **`data_engineer`** opera en **posición raíz** → ve todo por la **misma** política (NO `BYPASSRLS`): una sola regla, sin exenciones.

## Dónde aplica el RLS

- **`app`** (operativo) y **`gold`** (consumo externo) → política de subárbol.
- **`bronze`/`silver`** → no (cocina interna; sus dueños se saltan RLS igual).
- **`admin`** → no (se controla por grants).

## Cuándo se habilita

Es un **módulo listo y documentado, no forzado.** Un proyecto **mono-tenant** puede omitirlo. Para apps
multi-cliente (el caso típico), se habilita: tabla `app.tenants` + extensión `ltree` + la política de subárbol.

## Notas de implementación

- Indexar `path` con **GiST** para que el chequeo de subárbol no pese en cada consulta.
- La app es **responsable** de fijar `current_tenant` correcto tras el login; el **RLS lo aplica** (es la fuerza que no se puede olvidar).
- `SET LOCAL` limita el contexto a la transacción/petición → más seguro.
- Al ser la jerarquía bitemporal, una reorganización (mover una sucursal de cliente) queda **auditada y reconstruible**.
