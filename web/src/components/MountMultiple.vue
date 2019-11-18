<template>
  <q-card style="min-width: 900px">
    <q-card-section class="row items-center">
      <div class="text-h6">Choose Mount Parition</div>
      <q-space />
      <q-btn icon="close" flat round dense v-close-popup />
    </q-card-section>

    <q-form @submit.prevent="mountBackup">
      <q-card-section>This disk has multiple NTFS partions. Please choose one to mount</q-card-section>
      <q-card-section>
        <div v-for="(part, offset) in choices" :key="offset">
          <q-radio :val="offset" :label="part" v-model="offSet" />
          <br />
        </div>
      </q-card-section>
      <q-card-actions align="right">
        <q-btn label="Mount" color="primary" type="submit" />
        <q-btn label="Cancel" v-close-popup />
      </q-card-actions>
    </q-form>
  </q-card>
</template>

<script>
import axios from "axios";
import mixins from "@/mixins/mixins";

export default {
  name: "MountMultiple",
  mixins: [mixins],
  props: ["pk"],
  data() {
    return {
      offSet: null
    };
  },
  methods: {
    mountBackup() {
      if (!this.offSet) {
        this.notifyError("ERROR: Please select a parition");
      } else {
        this.$q.loading.show();
        axios.get(`/core/mountbyoffset/${this.pk}/${this.offSet}/`).then(r => {
          this.$q.loading.hide();
          this.$emit("close");
          this.$emit("refresh");
          this.notifySuccess("Backup was mounted!");
        })
        .catch(e => {
          this.$q.loading.hide();
          this.notifyError("Something went wrong")
        })
      }
    }
  },
  computed: {
    choices() {
      return this.$store.state.mountChoices;
    }
  }
};
</script>