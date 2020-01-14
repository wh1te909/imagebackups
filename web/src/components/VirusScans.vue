<template>
  <div class="q-pa-md q-gutter-sm">
    <q-dialog
      :value="toggleVirusScanModal"
      @hide="hideVirusScanModal"
      @show="getVirusScans"
      transition-show="slide-up"
      transition-hide="slide-down"
    >
      <q-card class="bg-grey-10 text-white" style="width: 1000px; max-width: 90vw">
        <q-bar>
            <q-btn @click="getVirusScans" class="q-mr-sm" dense flat push icon="refresh" label="Refresh" />
          Virus Scans
          <q-space />
          <q-btn dense flat icon="close" v-close-popup>
            <q-tooltip content-class="bg-white text-primary">Close</q-tooltip>
          </q-btn>
        </q-bar>
        <q-separator />
        <q-table
          :data="virusScans"
          :columns="columns"
          row-key="id"
          binary-state-sort
          :pagination.sync="pagination"
          :visible-columns="visibleColumns"
        >
            <template slot="body" slot-scope="props" :props="props">
                <q-tr>
                  <q-td>{{ props.row.backup_name }}</q-td>
                  <q-td>{{ props.row.started }}</q-td>
                  <!-- status -->
                  <q-td v-if="props.row.status === 'STARTED'">
                    <q-linear-progress indeterminate>
                      <q-tooltip>Scan is running</q-tooltip>
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
                      @click="viewVirusScanProgress(props.row.id)"
                    />
                    <q-btn
                      size="sm"
                      color="negative"
                      icon="delete"
                      @click="deleteVirusScan(props.row.id, props.row.backup_name)"
                    />
                  </q-td>
                  <q-td v-else-if="props.row.status === 'STARTED'" class="q-gutter-sm">
                    <q-btn
                      size="sm"
                      color="accent"
                      icon="remove_red_eye"
                      label="View Progress"
                      @click="viewVirusScanProgress(props.row.id)"
                    />
                    <q-btn
                      size="sm"
                      color="negative"
                      icon="cancel"
                      label="Cancel"
                      @click="cancelVirusScan(props.row.id)"
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
  name: "VirusScans",
  mixins: [mixins],
  data() {
    return {
        status: null,
        columns: [
            { name: "id", label: "ID", field: "id", sortable: false, align: "left"},
            { name: "backup_name", label: "Image", field: "backup_name", sortable: true, align: "left"},
            { name: "started", label: "Created at", field: "started", sortable: true, align: "left"},
            { name: "status", label: "Status", field: "Status", sortable: true, align: "left"},    
            { name: "action", label: "Action", align: "left" }
        ],
        visibleColumns: ["backup_name", "started", "status", "action"],
        pagination: {
            rowsPerPage: 20,
            sortBy: "id",
            descending: true
      }, 
    };
  },
  methods: {
    deleteVirusScan(pk, name) {
      this.$q.dialog({
        title: `Delete ${name} scan results?`,
        cancel: { label: "no", color: "negative" },
        ok: { label: "yes", color: "positive" }
      }).onOk(() => {
        this.$q.loading.show();
        axios.get(`/core/deletevirusscan/${pk}/`).then(r => {
          this.$q.loading.hide();
          this.getVirusScans();
          this.notifySuccess("Scan deleted!");
        })
        .catch(e => {
          this.$q.loading.hide();
          this.notifyError("Something went wrong")
        })
      })
    },
    cancelVirusScan(pk) {
      this.$q
        .dialog({
          title: `Cancel Scan`,
          message: "Cancel this running virus scan?",
          cancel: { label: "no", color: "negative" },
          persistent: true,
          ok: { label: "yes", color: "positive" }
        }).onOk(() => {
          this.$q.loading.show();
          axios.get(`/core/cancelvirusscan/${pk}`).then(r => {
            this.$q.loading.hide();
            this.notifySuccess("Scan was cancelled!");
            this.$emit("refresh");
          })
          .catch(e => {
            this.$q.loading.hide();
            this.notifyError(e.response.data.error);
            this.$emit("refresh");
          })
        })
    },
    viewVirusScanProgress(pk) {
      this.$q.loading.show();
      axios.get(`/core/viewvirusscanprogress/${pk}`).then(r => {
        this.$q.loading.hide();
        this.$q.dialog({
          message: `<pre>${r.data}</pre>`,
          //style: "width: 800px; max-width: 90vw",
          fullWidth: true,
          html: true
        });
      })
      .catch(e => {
        this.$q.loading.hide();
        this.notifyError("Something went wrong. Please try again")
      })
    },
    hideVirusScanModal() {
      this.$store.commit("TOGGLE_VIRUSSCAN_MODAL", false);
    },
    getVirusScans() {
        this.$emit("refresh");
    }
  },
  computed: {
    ...mapState({
      toggleVirusScanModal: state => state.toggleVirusScanModal,
      virusScans: state => state.virusScans
    })
  },
  created() {
      this.getVirusScans();
  }
};
</script>
