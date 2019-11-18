<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-grey-9 text-white">
      <q-toolbar>
        <q-btn dense flat push @click="getBackups" icon="refresh" />
        <q-toolbar-title>Tactical ImageBackups</q-toolbar-title>
        <q-toolbar-title><q-badge><code>{{ serverinfo.used }} used of {{ serverinfo.total }}</code></q-badge></q-toolbar-title>
        <q-btn-dropdown flat no-caps stretch :label="user">
          <q-list>
            <q-item clickable v-ripple>
              <q-item-section @click="shutdownServer">
                <q-item-label>Shutdown Server</q-item-label>
              </q-item-section>
            </q-item>
            <q-item to="/logout" exact>
              <q-item-section>
                <q-item-label>Logout</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-btn-dropdown>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <div class="q-pa-md">
        <div class="q-gutter-md">
          <q-btn
            v-if="backupsRunning || wipesRunning || diskcheckRunning"
            color="primary"
            disable
            label="Create Backup"
            icon="add"
            />
            
          <q-btn
            v-else
            color="primary"
            icon="add"
            label="Create Backup"
            @click="showCreateBackup = true"
          />
          
        
          <q-btn 
            v-if="wipesRunning" 
            label="Wipe Disk" 
            disable 
            color="negative" 
            icon="warning" 
          ><q-linear-progress indeterminate /></q-btn>
          <q-btn v-else-if="backupsRunning || diskcheckRunning" label="Wipe Disk" disable color="negative" icon="warning" />
          <q-btn v-else color="negative" label="Wipe Disk" icon="warning" @click="wipeDisk" />

          <q-btn v-if="wipesRunning" label="Cancel Wipe" color="accent" icon="stop" @click="cancelWipe(latestWipe)" />
          <q-btn v-if="wipesRunning" label="Wipe Status" color="secondary" icon="remove_red_eye" @click="viewWipeProgress" />

          <!-- Disk Check button -->
          <q-btn
            v-if="diskcheckRunning"
            color="info"
            icon="far fa-hdd"
            @click="showDiskCheckModal"
            label="Disk Check"
          ><q-linear-progress indeterminate /></q-btn>
          <q-btn
            v-else
            color="info"
            icon="far fa-hdd"
            @click="showDiskCheckModal"
            label="Disk Check"
          />

          <!-- Virus Scan button -->
          <q-btn
            v-if="virusScanRunning"
            color="accent"
            icon="cloud_circle"
            label="Virus Scans"
            @click="showVirusScanModal"
          ><q-linear-progress indeterminate /></q-btn>
          <q-btn
            v-else
            color="accent"
            icon="cloud_circle"
            label="Virus Scans"
            @click="showVirusScanModal"
          />

        </div>
        <br />
        <q-table
          :data="backups"
          :columns="columns"
          row-key="id"
          binary-state-sort
          :pagination.sync="pagination"
          :visible-columns="visibleColumns"
        >
          <template slot="body" slot-scope="props" :props="props">
            <q-tr>
              <q-td>{{ props.row.name }}</q-td>
              <q-td>{{ props.row.model }}</q-td>
              <q-td>{{ props.row.serial }}</q-td>
              <!-- status -->
              <q-td v-if="props.row.status === 'STARTED'">
                <q-linear-progress indeterminate>
                  <q-tooltip>Backup is running</q-tooltip>
                </q-linear-progress>
              </q-td>
              <q-td v-else-if="props.row.status === 'SUCCESS'">
                <q-icon name="check_circle" color="positive" size="md">
                  <q-tooltip>{{ props.row.status }}</q-tooltip>
                </q-icon>
              </q-td>
              <q-td v-else>{{ props.row.status }}</q-td>

              <!-- started time -->
              <q-td>{{ props.row.started }}</q-td>
              <!-- backup size -->
              <q-td><q-badge color="orange" text-color="black" :label="props.row.backup_size" /></q-td>
              <!-- actions -->
              <q-td v-if="props.row.status === 'SUCCESS'" class="q-gutter-sm">
                <q-btn
                  v-if="props.row.mounted"
                  size="sm"
                  color="positive"
                  icon="remove"
                  label="Un-mount"
                  @click="unMountBackup(props.row.id)"
                />
                <q-btn
                  v-else-if="props.row.virus_scan_running"
                  size="sm"
                  color="primary"
                  icon="add"
                  label="Mount"
                  disable
                />
                <q-btn
                  v-else
                  size="sm"
                  color="primary"
                  icon="add"
                  label="Mount"
                  @click="mountBackup(props.row.id)"
                />

                <!-- edit -->
                <q-btn v-if="props.row.mounted || props.row.virus_scan_running" disable size="sm" color="info" icon="edit" />
                <q-btn 
                  v-else
                  size="sm"
                  color="info"
                  icon="edit"
                  @click="renameBackup(props.row.id, props.row.name)"
                />

                <!-- virus scan -->
                <q-btn v-if="props.row.mounted" disable size="sm" color="accent" label="Scan" icon="cloud_circle" />
                <q-btn v-else-if="props.row.virus_scan_running" disable size="sm" color="accent" label="Scan" icon="cloud_circle">
                  <q-linear-progress indeterminate />
                </q-btn>
                <q-btn v-else-if="virusScanRunning" disable size="sm" color="accent" label="Scan" icon="cloud_circle" />
                <q-btn 
                  v-else
                  size="sm"
                  color="accent"
                  icon="cloud_circle"
                  label="Scan"
                  @click="virusScan(props.row.id)"
                />

                <!-- Delete -->
                <q-btn v-if="props.row.mounted || props.row.virus_scan_running" disable size="sm" color="negative" icon="delete" />
                <q-btn
                  v-else
                  size="sm"
                  color="negative"
                  icon="delete"
                  @click="deleteBackup(props.row.id, props.row.name)"
                />
              </q-td>
              <q-td v-else-if="props.row.status === 'STARTED'" class="q-gutter-sm">
                <q-btn
                  size="sm"
                  color="secondary"
                  icon="remove_red_eye"
                  label="Status"
                  @click="viewProgress(props.row.id)"
                 />
                <q-btn
                  size="sm"
                  color="accent"
                  icon="cancel"
                  label="Cancel"
                  @click="cancelBackup(props.row.id, props.row.name)"
                />
              </q-td>
              <q-td v-else class="q-gutter-sm"></q-td>
              <!-- mount point -->
              <q-td v-if="props.row.mounted">
                <code>\\10.0.27.142\Backups\{{ props.row.name }}</code>
              </q-td>
              <q-td v-else>n/a</q-td>
            </q-tr>
          </template>
        </q-table>
      </div>
    </q-page-container>

    <q-dialog v-model="showCreateBackup">
      <CreateBackup @close="showCreateBackup = false" @refresh="getBackups" />
    </q-dialog>
    <q-dialog v-model="showMountMultiple">
      <MountMultiple :pk="pkForMount" @close="showMountMultiple = false" @refresh="getBackups" />
    </q-dialog>
    <DiskCheck :backupsrunning="backupsRunning" :wipesrunning="wipesRunning" @refresh="getBackups"/>
    <VirusScans @refresh="getBackups" />
  </q-layout>
</template>

<script>
import axios from "axios";
import mixins from "@/mixins/mixins";
import { mapState } from "vuex";
import CreateBackup from "@/components/CreateBackup";
import MountMultiple from "@/components/MountMultiple";
import DiskCheck from "@/components/DiskCheck";
import VirusScans from "@/components/VirusScans";

export default {
  name: "home",
  components: {
    CreateBackup,
    MountMultiple,
    DiskCheck,
    VirusScans
  },
  mixins: [mixins],
  data() {
    return {
      showCreateBackup: false,
      showMountMultiple: false,
      pkForMount: null,
      backups: [],
      latestWipe: null,
      wipes: [],
      pagination: {
        rowsPerPage: 20,
        sortBy: "id",
        descending: true
      },
      visibleColumns: [
        "name",
        "model",
        "serial",
        "status",
        "started",
        "action",
        "mount",
        "backup_size"
      ],
      columns: [
        {
          name: "id",
          label: "ID",
          field: "id",
          sortable: false,
          align: "left"
        },
        {
          name: "name",
          label: "Backup Job",
          field: "name",
          sortable: true,
          align: "left"
        },
        {
          name: "model",
          label: "Model",
          field: "model",
          sortable: true,
          align: "left"
        },
        {
          name: "serial",
          label: "Serial",
          field: "serial",
          sortable: true,
          align: "left"
        },
        {
          name: "status",
          label: "Status",
          field: "status",
          sortable: true,
          align: "left"
        },
        {
          name: "started",
          label: "Created",
          field: "started",
          sortable: true,
          align: "left"
        },
        {
          name: "backup_size",
          label: "Backup Size",
          field: "backup_size",
          sortable: true,
          align: "left"
        },
        { name: "action", label: "Action", align: "left" },
        { name: "mount", label: "Mount", align: "left" }
      ]
    };
  },
  methods: {
    showDiskCheckModal() {
      this.$store.commit("TOGGLE_DISKCHECK_MODAL", true)
    },
    showVirusScanModal() {
      this.$store.commit("TOGGLE_VIRUSSCAN_MODAL", true)
    },
    renameBackup(pk, name) {
      this.$q.dialog({
        title: 'Rename',
        prompt: {
          model: name
        },
        cancel: true
      }).onOk(data => {
        const payload = {pk: pk, name: data}
        this.$q.loading.show();
        axios.post(`/core/rename/`, payload).then(r => {
          this.$q.loading.hide();
          this.notifySuccess("Backup was renamed!");
          this.getBackups();
        })
        .catch(e => {
          this.$q.loading.hide();
          this.notifyError(e.response.data.error);
        })
      })
    },
    cancelBackup(pk, name) {
      this.$q
        .dialog({
          title: `Cancel ${name}`,
          message: "Cancel and delete this running backup?",
          cancel: { label: "no", color: "negative" },
          persistent: true,
          ok: { label: "yes", color: "positive" }
        }).onOk(() => {
          this.$q.loading.show();
          axios.get(`/core/cancelbackup/${pk}`).then(r => {
            this.$q.loading.hide();
            this.notifySuccess("Backup was cancelled!");
            this.getBackups();
          })
          .catch(e => {
            this.$q.loading.hide();
            this.notifyError(e.response.data.error);
            this.getBackups();
          })
        })
    },
    shutdownServer() {
      this.$q.dialog({
        title: "Shutdown Server",
        message: "Shutdown the server?",
        cancel: { label: "no", color: "negative" },
        ok: { label: "yes", color: "positive" }
      })
      .onOk(() => {
        axios.get("/core/shutdownserver/").then(r => {
          this.notifySuccess("Server will now be shutdown")
        })
        .catch(e => {
          this.notifyError("Something went wrong")
        })
      })
    },
    deleteBackup(pk, name) {
      this.$q
        .dialog({
          title: `Delete ${name}`,
          message: "Are you sure you want to delete this image",
          cancel: { label: "no", color: "negative" },
          persistent: true,
          ok: { label: "yes", color: "positive" }
        })
        .onOk(() => {
          this.$q
            .dialog({
              title: `Please type <code style="color:red">${name}</code> to confirm`,
              prompt: { model: "", type: "text" },
              cancel: true,
              persistent: true,
              html: true
            })
            .onOk(nameConfirm => {
              if (nameConfirm !== name) {
                this.notifyError("ERROR: Please type the correct name!");
              } else {
                this.$q.loading.show();
                const data = { pk: pk };
                axios
                  .delete("/core/deletebackup/", { data: data })
                  .then(r => {
                    this.$q.loading.hide();
                    this.notifySuccess(`${name} deleted!`);
                    this.getBackups();
                  })
                  .catch(e => {
                    this.$q.loading.hide();
                    this.getBackups();
                    this.notifyError(e.response.data.error);
                  });
              }
            });
        });
    },
    cancelWipe(celeryID) {
      this.$q
        .dialog({
          title: "Cancel Wipe",
          message: "Cancel the disk wipe?",
          cancel: { label: "no", color: "negative" },
          ok: { label: "yes", color: "positive" }
        })
        .onOk(() => {
          this.$q.loading.show();
          axios
            .get(`/core/cancelwipe/${celeryID}/`)
            .then(r => {
              this.$q.loading.hide();
              this.notifySuccess("The wipe will be cancelled shortly. Please refresh soon");
              this.getBackups();
            })
            .catch(e => {
              this.$q.loading.hide();
              this.notifyError(e.response.data.error);
            });
        });
    },
    getWipes() {
      axios.get("/core/getwipes/").then(r => {
        this.wipes = r.data;
      });
    },
    getBackups() {
      axios.get("/core/getbackups/").then(r => {
        this.backups = r.data;
      });
      this.getWipes();
      this.getLatestWipe();
      this.$store.dispatch("serverInfo");
      this.$store.dispatch("getDiskChecks");
      this.$store.dispatch("getVirusScans");
    },
    virusScan(pk) {
      this.$q.dialog({
        title: "Scan for viruses",
        options: {
          type: "radio",
          model: "move",
          items: [
            {label: "Move infected files to quarantine", value: "move"},
            {label: "Copy infected files to quarantine", value: "copy"},
            {label: "Delete infected files", value: "delete"},
            {label: "Do nothing to files", value: "nothing"}
          ]
        },
        cancel: true
      })
      .onOk(data => {
        this.$q.loading.show();
        axios.get(`/core/virusscan/${pk}/${data}/`).then(r => {
          this.$q.loading.hide();
          this.getBackups();
          this.notifySuccess("Scan Started!");
          this.$store.commit("TOGGLE_VIRUSSCAN_MODAL", true);
        })
        .catch(e => {
          this.$q.loading.hide();
          this.getBackups();
          this.notifyError(e.response.data.error);
        })
      })
    },
    mountBackup(pk) {
      this.$q.loading.show();
      axios
        .get(`/core/mountbackup/${pk}/`)
        .then(r => {
          if (r.data === "oneparitiononly") {
            this.$q.loading.hide();
            this.notifySuccess("Backup was mounted!");
            this.getBackups();
          } else {
            this.$q.loading.hide();
            this.pkForMount = pk;
            this.$store.commit("SET_MOUNT_CHOICES", r.data);
            this.showMountMultiple = true;
          }
        })
        .catch(e => {
          this.$q.loading.hide();
          this.notifyError("Something went wrong");
        });
    },
    unMountBackup(pk) {
      this.$q.loading.show();
      axios
        .get(`/core/unmountbackup/${pk}`)
        .then(r => {
          this.$q.loading.hide();
          this.notifySuccess("Backup unmounted!");
          this.getBackups();
        })
        .catch(e => {
          this.notifyError("Something went wrong");
          this.$q.loading.hide();
        });
    },
    viewProgress(pk) {
      this.$q.loading.show();
      axios.get(`/core/viewprogress/${pk}`).then(r => {
        this.$q.loading.hide();
        this.$q.dialog({
          message: `<pre>${r.data}</pre>`,
          style: "width: 800px; max-width: 90vw",
          html: true
        });
      })
      .catch(e => {
        this.$q.loading.hide();
        this.notifyError("Something went wrong. Please try again")
      })
    },
    getLatestWipe() {
      axios.get("/core/getlatestwipe/").then(r => this.latestWipe = r.data);
    },
    viewWipeProgress() {
      this.$q.loading.show();
      axios.get('/core/wipeprogress/').then(r => {
        this.$q.loading.hide();
        if (r.data === 'wipefinished') {
          this.notifyError("Wipe already finished! Please refresh.");
          this.getBackups();
          return;
        }
        
        this.$q.dialog({
          message: `<pre>${r.data}</pre>`,
          style: "width: 800px; max-width: 90vw",
          html: true
        });
      })
      .catch(e => {
        this.$q.loading.hide();
        this.notifyError("Something went wrong. Please try again")
      })
    },
    wipeDisk() {
      this.$q
        .dialog({
          title: "Wipe Disk",
          message: "Are you sure you want to wipe the disk in bay 4?",
          cancel: { label: "no", color: "negative" },
          persistent: true,
          ok: { label: "yes", color: "positive" }
        })
        .onOk(() => {
          this.$q
            .dialog({
              title: "DANGER AHEAD",
              message: "Once again, are you sure you want to wipe the disk?",
              cancel: { label: "no", color: "negative" },
              persistent: true,
              ok: { label: "DESTROY IT!!!", color: "positive" }
            })
            .onOk(() => {
              this.$q.loading.show();
              axios
                .get("/core/wipedisk/")
                .then(r => {
                  this.$q.loading.hide();
                  this.notifySuccess("Wipe started!");
                  this.getBackups();
                })
                .catch(e => {
                  this.$q.loading.hide();
                  this.notifyError(e.response.data.error);
                });
            });
        });
    }
  },
  computed: {
    ...mapState({
      user: state => state.username,
      serverinfo: state => state.serverInfo,
      diskChecks: state => state.diskChecks,
      virusScans: state => state.virusScans
    }),
    backupsRunning() {
      const running = this.backups.find(k => k.status === 'STARTED');
      if (running) {
        return true;
      } else {
        return false
      }
    },
    wipesRunning() {
      const running = this.wipes.find(k => k.status === 'STARTED');
      if (running) {
        return true;
      } else {
        return false
      }
    },
    diskcheckRunning() {
      const running = this.diskChecks.find(k => k.status === 'STARTED');
      if (running) {
        return true;
      } else {
        return false
      }
    },
    virusScanRunning() {
      const running = this.virusScans.find(k => k.status === 'STARTED');
      if (running) {
        return true;
      } else {
        return false
      }
    }
  },
  created() {
    this.$q.dark.set(true);
    this.getBackups();
  }
};
</script>
