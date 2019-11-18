<template>
  <div class="q-pa-md">
    <div class="row text-center">
      <div class="col"></div>
      <div class="col">
        <h5>Tactical ImageBackups</h5>
        <q-form @submit="onSubmit" class="q-gutter-md">
          <q-input
            outlined
            v-model="credentials.username"
            label="Username"
            lazy-rules
            :rules="[ val => val && val.length > 0 || 'This field is required']"
          />

          <q-input
            outlined
            type="password"
            v-model="credentials.password"
            label="Password"
            lazy-rules
            :rules="[ val => val && val.length > 0 || 'This field is required']"
          />

          <div>
            <q-btn label="Login" type="submit" color="primary" class="full-width q-mt-md" />
          </div>
        </q-form>
      </div>
      <div class="col"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: "Login",
  data() {
    return {
      credentials: {}
    };
  },

  methods: {
    onSubmit() {
      this.$store.dispatch("retrieveToken", this.credentials).then(response => {
        this.$router.push({ name: "home" });
      });
    }
  },
  created() {
      this.$q.dark.set(true);
  }
};
</script>