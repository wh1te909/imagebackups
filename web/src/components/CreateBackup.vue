<template>
  <q-card style="min-width: 900px">
    <q-card-section class="row items-center">
      <div class="text-h6">Create Backup</div>
      <q-space />
      <q-btn icon="close" flat round dense v-close-popup />
    </q-card-section>

    <q-form @submit.prevent="createBackup">
      <q-card-section>
        <pre>{{ diskInfo }}</pre>
      </q-card-section>
      <q-card-section>
        <q-input
          outlined
          v-model="backupName"
          label="Name of backup"
          :rules="[ val => !!val || '*Required']"
        />
      </q-card-section>
      <q-card-actions align="right">
        <q-btn label="Start" color="primary" type="submit" />
        <q-btn label="Cancel" v-close-popup />
      </q-card-actions>
    </q-form>
    <q-inner-loading :showing="visible">
      <q-spinner size="40px" color="primary" />
    </q-inner-loading>
  </q-card>
</template>

<script>
import axios from "axios";
import mixins from "@/mixins/mixins";

export default {
  name: "CreateBackup",
  mixins: [mixins],
  data() {
    return {
      backupName: null,
      diskInfo: null,
      visible: false
    };
  },
  methods: {
    createBackup() {
      this.$q.loading.show();
      const data = { backupname: this.backupName };
      axios.post("/core/createbackup/", data).then(r => {
        this.$q.loading.hide();
        this.$emit("close");
        this.$emit("refresh");
      })
      .catch(e => {
        this.$q.loading.hide();
        this.notifyError(e.response.data.error);
      })
    },
    getDisk() {
      this.visible = true;
      axios.get("/core/getdisk/").then(r => {
        this.diskInfo = r.data;
        this.visible = false;
      })
      .catch(e => {
        this.visible = false;
      })
    }
  },
  mounted() {
    this.getDisk();
  }
};
</script>