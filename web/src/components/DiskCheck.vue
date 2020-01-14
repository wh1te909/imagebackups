<template>
  <div class="q-pa-md q-gutter-sm">
    <q-dialog
      :value="toggleDiskCheckModal"
      @hide="hideDiskCheckModal"
      @show="getDiskChecks"
      transition-show="slide-up"
      transition-hide="slide-down"
    >
      <q-card class="bg-grey-10 text-white" style="width: 1000px; max-width: 90vw">
        <q-bar>
            <q-btn @click="getDiskChecks" class="q-mr-sm" dense flat push icon="refresh" label="Refresh" />
          Disk Checks
          <q-space />
          <q-btn dense flat icon="close" v-close-popup>
            <q-tooltip content-class="bg-white text-primary">Close</q-tooltip>
          </q-btn>
        </q-bar>
        <div class="q-pa-md row">
          <q-btn v-if="backupsrunning || wipesrunning || diskcheckRunning || clonerunning" label="Start Disk Check" disable color="primary" icon="add" />
          <q-btn v-else color="primary" icon="add" @click="startDiskCheck" label="Start Disk Check" />
        </div>
        <q-separator />
        <q-table
          :data="diskChecks"
          :columns="columns"
          row-key="id"
          binary-state-sort
          :pagination.sync="pagination"
          :visible-columns="visibleColumns"
        >
            <template slot="body" slot-scope="props" :props="props">
                <q-tr>
                  <q-td>{{ props.row.model }}</q-td>
                  <q-td>{{ props.row.serial }}</q-td>
                  <q-td>{{ props.row.started }}</q-td>
                  <!-- status -->
                  <q-td v-if="props.row.status === 'STARTED'">
                    <q-linear-progress indeterminate>
                      <q-tooltip>Diskcheck is running</q-tooltip>
                    </q-linear-progress>
                  </q-td>
                  <q-td v-else-if="props.row.status === 'SUCCESS'">
                    <q-icon name="check_circle" color="positive" size="md">
                      <q-tooltip>{{ props.row.status }}</q-tooltip>
                    </q-icon>
                  </q-td>
                  <q-td v-else>{{ props.row.status }}</q-td>

                  <q-td v-if="props.row.status === 'SUCCESS'" class="q-gutter-sm">
                    <q-btn
                      size="sm"
                      color="positive"
                      icon="remove_red_eye"
                      label="Results"
                      @click="viewDiskCheckProgress(props.row.id)"
                    />
                  </q-td>
                  <q-td v-else-if="props.row.status === 'STARTED'" class="q-gutter-sm">
                    <q-btn
                      size="sm"
                      color="accent"
                      icon="remove_red_eye"
                      label="View Progress"
                      @click="viewDiskCheckProgress(props.row.id)"
                    />
                    <q-btn
                      size="sm"
                      color="negative"
                      icon="cancel"
                      label="Cancel"
                      @click="cancelDiskCheck(props.row.celery_id)"
                    />
                  </q-td>
                  <q-td v-else class="q-gutter-sm"></q-td>
                </q-tr>
            </template>
        </q-table>
      </q-card>
    </q-dialog>
  </div>
</template>

<script>
import axios from "axios";
import { mapState } from 'vuex';
import mixins from "@/mixins/mixins";
export default {
  name: "DiskCheck",
  mixins: [mixins],
  props: ["backupsrunning", "wipesrunning", "clonerunning"],
  data() {
    return {
        status: null,
        columns: [
            { name: "id", label: "ID", field: "id", sortable: false, align: "left"},
            { name: "model", label: "Model", field: "model", sortable: true, align: "left"},
            { name: "serial", label: "Serial", field: "serial", sortable: true, align: "left"},
            { name: "started", label: "Created at", field: "started", sortable: true, align: "left"},
            { name: "status", label: "Status", field: "Status", sortable: true, align: "left"},    
            { name: "action", label: "Action", align: "left" }
        ],
        visibleColumns: ["model", "serial", "status", "started", "action"],
        pagination: {
            rowsPerPage: 20,
            sortBy: "id",
            descending: true
      }, 
    };
  },
  methods: {
    cancelDiskCheck(celeryid) {
      this.$q
        .dialog({
          title: `Cancel DiskCheck`,
          message: "Cancel this running disk check?",
          cancel: { label: "no", color: "negative" },
          persistent: true,
          ok: { label: "yes", color: "positive" }
        }).onOk(() => {
          this.$q.loading.show();
          axios.get(`/core/canceldiskcheck/${celeryid}`).then(r => {
            this.$q.loading.hide();
            this.notifySuccess("Disk check cancelled!");
            this.$emit("refresh");
          })
          .catch(e => {
            this.$q.loading.hide();
            this.notifyError("Something went wrong");
            this.$emit("refresh");
          })
        })
    },
    viewDiskCheckProgress(pk) {
      this.$q.loading.show();
      axios.get(`/core/viewdiskcheckprogress/${pk}`).then(r => {
        this.$q.loading.hide();
        this.$q.dialog({
          message: `<pre>${r.data}</pre>`,
          style: "width: 800px; max-width: 90vw; height: 600px; max-height: 50vw;",
          html: true
        });
      })
      .catch(e => {
        this.$q.loading.hide();
        this.notifyError("Something went wrong. Please try again")
      })
    },
    hideDiskCheckModal() {
      this.$store.commit("TOGGLE_DISKCHECK_MODAL", false);
    },
    getDiskChecks() {
        this.$store.dispatch("getDiskChecks");
    },
    startDiskCheck() {
        this.$q.loading.show();
        axios.get("/core/getdisk/").then(r => {
            this.$q.loading.hide();
            this.$q.dialog({
                title: 'Disk Check',
                message: `<pre>${r.data}</pre>`,
                style: "width: 800px; max-width: 90vw",
                html: true,
                cancel: true,
                ok: { label: "Start Disk Check", color: "info" }
            }).onOk(() => {
                this.$q.loading.show();
                axios.get("/core/startdiskcheck/").then(r => {
                    this.$q.loading.hide();
                    this.getDiskChecks();
                    this.notifySuccess("Disk check started!")
                })
                .catch(e => {
                    this.$q.loading.hide();
                    this.notifyError(e.response.data.error);
                })
            })
        })
        .catch(e => {
            this.$q.loading.hide();
            this.notifyError("Something went wrong");
        })
    }
  },
  computed: {
    ...mapState({
      toggleDiskCheckModal: state => state.toggleDiskCheckModal,
      diskChecks: state => state.diskChecks
    }),
    diskcheckRunning() {
      const running = this.diskChecks.find(k => k.status === 'STARTED');
      if (running) {
        return true;
      } else {
        return false
      }
    }
  },
  created() {
      this.getDiskChecks();
  }
};
</script>
