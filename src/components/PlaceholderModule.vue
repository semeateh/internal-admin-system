<template>
  <section class="placeholder">
    <div>
      <h2>{{ moduleTitle }}</h2>
      <p>这里后续可以扩展为独立后台模块。</p>
    </div>
  </section>
</template>

<script>
export default {
  name: "PlaceholderModule",
  props: {
    moduleTitle: {
      type: String,
      default: "模块建设中"
    }
  }
};
</script>
