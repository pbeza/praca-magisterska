# mySCM #

This project is a part of the master thesis that implements simple [Software Configuration Management tool (SCM)][1] for [Unix-like][2] system, specifically for [Debian][3] and [Linux Arch][4]. This project is intended to be ([yet another][5]) light alternative for big SCMs like [Puppet][6], [Chef][7], [Ansible][8], [Salt][9] and [other][5] existing solutions.

### Architecture ###

This is main directory that contains source code of the whole project. Application consists of 2 parts:

* **Server** – that is reference software and configuration model for clients. Server is responsible for:
    * scanning and detecting server's software and configuration changes using [AIDE][10],
    * generating [GNU/Linux][11] system image that will be applied by the clients.
* **Client** – that is machine that software and configuration will be modified to match server's system image. Client is responsible for:
    * applying system image prepared by the server,
    * downloading system image that will be applied on client's machine,
    * sharing the system image with other clients.

### Implementation ###

This project is implemented in [Python][12] [3.6][13] exclusively.

[1]:https://en.wikipedia.org/wiki/Software_configuration_management
[2]:https://en.wikipedia.org/wiki/Unix-like
[3]:https://www.debian.org/
[4]:https://www.archlinux.org/
[5]:https://en.wikipedia.org/wiki/Comparison_of_open-source_configuration_management_software
[6]:https://puppet.com/
[7]:https://www.chef.io/
[8]:https://www.ansible.com/
[9]:https://saltstack.com/
[10]:http://aide.sourceforge.net/
[11]:https://www.gnu.org/gnu/why-gnu-linux.html
[12]:https://www.python.org/
[13]:https://docs.python.org/3.6/
