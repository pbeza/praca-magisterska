PYTHON=python3
MAKE=make
MYSCM-CLI_DIR=myscm-cli
MYSCM-SRV_DIR=myscm-srv
MYSCM-COMMON_DIR=myscm-common
MYSCM_TMP_DIR=/tmp/myscm
MYSCM_CONFIG_TMP_DIR=$(MYSCM_TMP_DIR)/config

.PHONY: all build dist list clean copy2tmp

all: build copy2tmp

build:
	$(MAKE) -C $(MYSCM-COMMON_DIR) build
	$(MAKE) -C $(MYSCM-CLI_DIR) build
	$(MAKE) -C $(MYSCM-SRV_DIR) build

dist:
	$(MAKE) -C $(MYSCM-COMMON_DIR) dist
	$(MAKE) -C $(MYSCM-CLI_DIR) dist
	$(MAKE) -C $(MYSCM-SRV_DIR) dist

list:
	$(MAKE) -C $(MYSCM-COMMON_DIR) list
	$(MAKE) -C $(MYSCM-CLI_DIR) list
	$(MAKE) -C $(MYSCM-SRV_DIR) list

copy2tmp:
	mkdir -p $(MYSCM_TMP_DIR)
	-cp myscm-common/deb_dist/*.deb $(MYSCM_TMP_DIR)
	-cp myscm-cli/deb_dist/*.deb $(MYSCM_TMP_DIR)
	-cp myscm-srv/deb_dist/*.deb $(MYSCM_TMP_DIR)
	mkdir -p $(MYSCM_CONFIG_TMP_DIR)
	-cp myscm-cli/myscm/client/config/security/myscm-srv.cert.pub.pem $(MYSCM_CONFIG_TMP_DIR)
	-cp myscm-cli/myscm/client/config/security/myscm-srv.cert.pem $(MYSCM_CONFIG_TMP_DIR)
	-cp myscm-srv/myscm/server/config/security/myscm-srv.cert.priv.pem $(MYSCM_CONFIG_TMP_DIR)

clean:
	$(MAKE) -C $(MYSCM-COMMON_DIR) clean
	$(MAKE) -C $(MYSCM-CLI_DIR) clean
	$(MAKE) -C $(MYSCM-SRV_DIR) clean
