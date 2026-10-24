<!--
====================================================================
 02 — ALCANCE  ·  Nivel 1 (Constitución)
--------------------------------------------------------------------
 ESTE ARCHIVO ES POR-PROYECTO. Scaffold: responde cada sección y borra
 las guías (> …) y el ejemplo comentado.
 El alcance es la frontera del propósito (00). Lo más valioso aquí NO es
 lo que entra, sino lo que se decide dejar FUERA a propósito.
====================================================================
-->

# 02 — Alcance

## Dentro (in-scope)

> Las capacidades que este proyecto **sí** cubre. Verbos concretos, no áreas vagas.
> Cada una debería poder convertirse luego en una feature (`spec/features/NNN_...`).

- _(Capacidad 1.)_
- _(Capacidad 2.)_

## Fuera (out-of-scope) — explícito

> Lo que **deliberadamente NO** hacemos, aunque parezca cercano. Esta lista evita el *scope creep*
> y las discusiones futuras ("¿no íbamos a…?"). Si algo es "quizás después", va aquí, no en Dentro.

- _(No-objetivo 1 — y por qué queda fuera.)_
- _(No-objetivo 2.)_

<!--
EJEMPLO (ficticio, borrar):
 Dentro:  registro de envíos, cálculo de costo por ruta, panel de estado en vivo.
 Fuera:   facturación electrónica (lo hace otro sistema), app móvil nativa (v1 es web),
          optimización automática de rutas (fase futura, no ahora).
-->

## Supuestos

> Lo que damos por cierto para que el proyecto tenga sentido. Si un supuesto cae, el alcance cambia.

- _(Supuesto 1.)_

## Restricciones

> Límites no técnicos que acotan el proyecto: presupuesto, plazos, regulación, privacidad de datos,
> integraciones obligatorias. (Las restricciones **técnicas** van en `03_stack`.)

- _(Restricción 1.)_

## Fronteras del sistema

> Con **qué sistemas externos** se integra y quién es dueño de qué dato. Marca dónde termina
> nuestra responsabilidad. Útil para definir contratos transversales (`spec/contracts/`).

- _(Integración / frontera 1.)_
