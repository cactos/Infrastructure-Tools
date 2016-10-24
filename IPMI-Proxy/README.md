# Openstack IPMI Proxy 
 * Clients are e.g. the CACTOS VMI Controller, executing OptimisationPlans and need to power on/off compute nodes
 * This proxy accepts the following tcp messages:
```
$AUTH_TOKEN $action $host
$AUTH_TOKEN status <node_hostname>
$AUTH_TOKEN on <node_hostname>
$AUTH_TOKEN off <node_hostname>
```