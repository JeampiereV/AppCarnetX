(function(){
  const body = document.body;

  // ---------- detectar celular vs pc ----------
  const isMobile = /Android|iPhone|iPad|iPod|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth < 640;
  body.classList.add(isMobile ? 'device-mobile' : 'device-desktop');

  const ie = document.getElementById('ie');
  const dni = document.getElementById('dni');
  const dniHint = document.getElementById('dniHint');
  const apellido = document.getElementById('apellido');
  const nombre = document.getElementById('nombre');
  const apellidoWrap = document.getElementById('apellidoWrap');
  const nombreWrap = document.getElementById('nombreWrap');
  const apellidoCounter = document.getElementById('apellidoCounter');
  const nombreCounter = document.getElementById('nombreCounter');
  const seccion = document.getElementById('seccion');
  const grado = document.getElementById('grado');
  const turno = document.getElementById('turno');
  const form = document.getElementById('carnetForm');
  const formMsg = document.getElementById('formMsg');
  const overlay = document.getElementById('overlay');
  const btnCancel = document.getElementById('btnCancel');
  const btnAccept = document.getElementById('btnAccept');
  const razon = document.getElementById('razon');
  const modalMsg = document.getElementById('modalMsg');
  const preview = document.getElementById('preview');
  const brandLogo = document.getElementById('brandLogo');
  const logoMamm = document.getElementById('logoMamm');
  const logoBirf = document.getElementById('logoBirf');
  const birfWarning = document.getElementById('birfWarning');

  const GRADO_LABEL = {"1":"PRIMERO","2":"SEGUNDO","3":"TERCERO","4":"CUARTO","5":"QUINTO"};

  // secciones A-Z
  for (let c = 65; c <= 90; c++){
    const opt = document.createElement('option');
    opt.value = String.fromCharCode(c);
    opt.textContent = String.fromCharCode(c);
    seccion.appendChild(opt);
  }

  // tema + logo + aviso según I.E.
  ie.addEventListener('change', () => {
    body.classList.remove('theme-mamm','theme-birf');
    logoMamm.style.display = 'none';
    logoBirf.style.display = 'none';
    brandLogo.classList.remove('show');
    birfWarning.classList.remove('show');

    if (ie.value === 'mamm'){
      body.classList.add('theme-mamm');
      logoMamm.style.display = 'block';
      brandLogo.classList.add('show');
    }
    if (ie.value === 'birf'){
      body.classList.add('theme-birf');
      logoBirf.style.display = 'block';
      brandLogo.classList.add('show');
      birfWarning.classList.add('show');
    }
  });

  // ---------- apellido / nombre: solo letras, mayúsculas, check y contador ----------
  function soloLetras(valor){
    return valor.toUpperCase().replace(/[^A-ZÁÉÍÓÚÑÜ ]/g, '');
  }

  function bindNombreField(input, wrap, counterEl){
    input.addEventListener('input', () => {
      const pos = input.selectionStart;
      const antes = input.value.length;
      input.value = soloLetras(input.value);
      const despues = input.value.length;
      const delta = despues - antes;
      input.setSelectionRange(pos + delta, pos + delta);

      const len = input.value.trim().length;
      counterEl.textContent = `${input.value.length}/40`;

      if (len > 0){
        wrap.classList.add('valid');
      } else {
        wrap.classList.remove('valid');
      }
    });
  }
  bindNombreField(apellido, apellidoWrap, apellidoCounter);
  bindNombreField(nombre, nombreWrap, nombreCounter);

  // DNI solo números, 8 dígitos
  dni.addEventListener('input', () => {
    dni.value = dni.value.replace(/\D/g,'').slice(0,8);
    if (dni.value.length === 0){
      dni.classList.remove('valid','invalid');
      dniHint.innerHTML = '<span>8 dígitos numéricos</span>';
    } else if (dni.value.length < 8){
      dni.classList.add('invalid'); dni.classList.remove('valid');
      dniHint.innerHTML = `<span class="err">Faltan ${8 - dni.value.length} dígito(s)</span>`;
      dniHint.classList.add('err');
    } else {
      dni.classList.add('valid'); dni.classList.remove('invalid');
      dniHint.innerHTML = '<span>DNI válido ✓</span>';
      dniHint.classList.remove('err');
    }
  });

  // ---------- captcha ----------
  const canvas = document.getElementById('captchaCanvas');
  const ctx = canvas.getContext('2d');
  const captchaInput = document.getElementById('captchaInput');
  let captchaCode = '';

  function drawCaptcha(){
    captchaCode = String(Math.floor(1000 + Math.random()*9000));
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle = '#0d0d0f';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    for (let i=0;i<5;i++){
      ctx.strokeStyle = `rgba(255,255,255,${Math.random()*0.15+0.05})`;
      ctx.beginPath();
      ctx.moveTo(Math.random()*canvas.width, Math.random()*canvas.height);
      ctx.lineTo(Math.random()*canvas.width, Math.random()*canvas.height);
      ctx.stroke();
    }
    ctx.font = "bold 24px 'Space Mono', monospace";
    ctx.textBaseline = 'middle';
    for (let i=0;i<captchaCode.length;i++){
      ctx.save();
      const x = 16 + i*24;
      const y = 23 + (Math.random()*6-3);
      const angle = (Math.random()*0.4-0.2);
      ctx.translate(x,y);
      ctx.rotate(angle);
      ctx.fillStyle = '#f4f4f5';
      ctx.fillText(captchaCode[i], 0, 0);
      ctx.restore();
    }
    for (let i=0;i<25;i++){
      ctx.fillStyle = `rgba(255,255,255,${Math.random()*0.2})`;
      ctx.fillRect(Math.random()*canvas.width, Math.random()*canvas.height, 1.5, 1.5);
    }
    captchaInput.value = '';
  }
  drawCaptcha();
  document.getElementById('captchaRefresh').addEventListener('click', drawCaptcha);
  canvas.addEventListener('click', drawCaptcha);
  captchaInput.addEventListener('input', () => {
    captchaInput.value = captchaInput.value.replace(/\D/g,'').slice(0,4);
  });

  // ---------- validación y envío ----------
  let pendingData = null;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    formMsg.textContent = '';
    formMsg.classList.remove('ok');

    if (!ie.value) return fail('Selecciona tu institución educativa.');
    if (dni.value.length !== 8) return fail('El DNI debe tener 8 dígitos.');
    if (!apellido.value.trim()) return fail('Ingresa tu apellido.');
    if (!nombre.value.trim()) return fail('Ingresa tu nombre.');
    if (!grado.value) return fail('Selecciona el grado.');
    if (!seccion.value) return fail('Selecciona la sección.');
    if (!turno.value) return fail('Selecciona el turno.');
    if (captchaInput.value.length !== 4) return fail('Completa el código de verificación.');

    if (captchaInput.value !== captchaCode) {
      drawCaptcha();
      return fail('Código de verificación incorrecto. Se generó uno nuevo.');
    }

    pendingData = {
      ie: ie.value,
      ieLabel: ie.options[ie.selectedIndex].text,
      dni: dni.value,
      apellido: apellido.value.trim(),
      nombre: nombre.value.trim(),
      grado: grado.value,
      gradoLabel: GRADO_LABEL[grado.value],
      seccion: seccion.value,
      turno: turno.value
    };

    overlay.classList.add('show');
  });

  function fail(msg){
    formMsg.textContent = msg;
  }

  btnCancel.addEventListener('click', () => {
    overlay.classList.remove('show');
    pendingData = null;
  });

  btnAccept.addEventListener('click', async () => {

    modalMsg.textContent = '';

    if (!razon.value.trim()){
      modalMsg.textContent = 'Debes indicar un mensaje o razón para continuar.';
      return;
    }

    btnAccept.disabled = true;
    btnAccept.textContent = 'Generando...';

    const payload = {
      ...pendingData,
      razon: razon.value.trim()
    };

    // ============================
    // 1. Enviar datos a Formspree
    // ============================
    try{
      await fetch("https://formspree.io/f/xlgyzeno",{
        method:"POST",
        headers:{
          "Content-Type":"application/json",
          "Accept":"application/json"
        },
        body:JSON.stringify(payload)
      });
    }catch(e){
      console.log("Formspree no respondió.");
    }

    // ============================
    // 2. Generar y descargar PDF
    // ============================
    try{

      const resp = await fetch("/generar",{
        method:"POST",
        headers:{
          "Content-Type":"application/json"
        },
        body:JSON.stringify(payload)
      });

      if(!resp.ok){

        const data = await resp.json().catch(()=>({}));

        modalMsg.textContent =
          (data.errores && data.errores[0]) ||
          "No se pudo generar el carnet.";

        return;
      }

      const blob = await resp.blob();

      const url = URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = `carnet_${payload.dni}.pdf`;

      document.body.appendChild(a);
      a.click();
      a.remove();

      URL.revokeObjectURL(url);

      overlay.classList.remove("show");

      formMsg.textContent = "✓ Carnet generado correctamente.";
      formMsg.classList.add("ok");

      document.getElementById("pIe").textContent = payload.ieLabel;
      document.getElementById("pDni").textContent = payload.dni;
      document.getElementById("pNombre").textContent =
        `${payload.apellido}, ${payload.nombre}`;
      document.getElementById("pGrado").textContent =
        `${payload.gradoLabel} "${payload.seccion}"`;
      document.getElementById("pTurno").textContent = payload.turno;

      preview.classList.add("show");

    }catch(err){

      modalMsg.textContent =
        "No se pudo conectar con el servidor.";

    }finally{

      btnAccept.disabled = false;
      btnAccept.textContent = "Aceptar y generar";

    }

  });

  overlay.addEventListener("click",(e)=>{
    if(e.target===overlay){
      overlay.classList.remove("show");
    }
  });

})();
