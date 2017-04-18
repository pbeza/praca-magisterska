# mySCM #

This project is part of the master thesis and implements simple [Software Configuration Management tool (SCM)][1] for Unix-like system, specifically for [Debian][2] and [Linux Arch][3]. This project is intended to be ([yet another][4]) light alternative for big SCMs like [Puppet][5], [Chef][6], [Ansible][7], [Salt][8] and [other][4] existing solutions.

### Architecture ###

This is main directory with source code of the whole project which consists of two parts:

* **Server** – responsible for:
    * multicasting clients' configuration,
    * providing [package repository proxy][9] for clients,
    * collecting logs sent by clients after applying changes by them.
* **Client** – responsible for interpreting, applying changes sent from server and sending logs to the server.

### Implementation ###

This project is implemented in [Python][10] [3.6][11].

[1]:https://en.wikipedia.org/wiki/Software_configuration_management
[2]:https://www.debian.org/
[3]:https://www.archlinux.org/
[4]:https://en.wikipedia.org/wiki/Comparison_of_open-source_configuration_management_software
[5]:https://puppet.com/
[6]:https://www.chef.io/
[7]:https://www.ansible.com/
[8]:https://saltstack.com/
[9]:https://lwn.net/Articles/318658/
[10]:https://www.python.org/
[11]:https://docs.python.org/3.6/
