<template>
  <div class="background-container">
    <div class="background-shapes">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
      <div class="circle circle-4"></div>
      <div class="circle circle-5"></div>
      <div class="circle circle-6"></div>
      <div class="circle circle-7"></div>
      <div class="circle circle-8"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BackGround'
}
</script>

<style scoped>
.background-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  overflow: hidden;
}

.background-shapes {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.circle {
  border-radius: 50%;
  background-color: rgba(210, 240, 210, 0.6);
  position: absolute;
}

.circle-1 {
  width: 500px;
  height: 500px;
  top: -220px;
  left: 790px;
}

.circle-2 {
  width: 500px;
  height: 500px;
  top: -90px;
  left: 1080px;
}

.circle-3 {
  width: 500px;
  height: 500px;
  top: -350px;
  left: 0px;
}

.circle-4 {
  width: 500px;
  height: 500px;
  bottom: -250px;
  left: 0px;
}

.circle-5 {
  width: 500px;
  height: 500px;
  bottom: -150px;
  right: -50px;
}

.circle-6 {
  width: 100px;
  height: 100px;
  top: 15%;
  left: 40%;
}

.circle-7 {
  width: 80px;
  height: 80px;
  top: 35%;
  left: 10%;
}

.circle-8 {
  width: 70px;
  height: 70px;
  top: 75%;
  left: 45%;
}
</style>