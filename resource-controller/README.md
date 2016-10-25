# controller

This project realises a very simple resource controller that enforces constraints on
the amount of physical resources a virtual machine is allowed to consume. As of now,
only CPU is supported. The enforcement is realised via cgroups.
FIXME: description

## Installation

Download from http://example.com/FIXME.

## Usage

FIXME: explanation

    $ java -jar controller-0.1.0-standalone.jar [args]

## Options

This application does not accept any arguments or options.

## Examples

TBD ...

### Bugs and Shortcomings

This projects has only been implemented (and tested) for virtual machines 
running on a kvm hypervisor under a CentOS 7 hypervisor.

## License

Copyright © 2016 Jörg Domaschka, Ulm University, Germany

Distributed under the Eclipse Public License either version 1.0 or (at
your option) any later version.
