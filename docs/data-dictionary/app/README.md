# Diccionario — schema `app` (OLTP)

Una entrada por tabla del schema transaccional. Plantilla por tabla:

```
### app.<tabla>
- Propósito:
- ¿Bitemporal?:  sí/no   (si sí: valid_time + transaction_time)
- ¿PII?:         columnas sensibles y su tratamiento (omit/mask/hash)
- ¿Tenant-scoped (RLS)?:  sí/no
- Columnas:  nombre — tipo — significado
```
