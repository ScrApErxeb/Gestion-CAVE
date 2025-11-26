let consommationsSelectionnees = [];

document.addEventListener('DOMContentLoaded', () => {
    chargerAbonnes();
    chargerFactures();
});

async function chargerAbonnes() {
    try {
        const res = await fetch('/api/abonnes');
        const data = await res.json();
        if(data.success) {
            const select = document.getElementById('abonneFacture');
            data.data.forEach(a => {
                const option = document.createElement('option');
                option.value = a.id;
                option.textContent = `${a.numero_abonne} - ${a.nom_complet}`;
                select.appendChild(option);
            });
        }
    } catch(e){ console.error(e); }
}

async function chargerFactures() {
    try {
        const statut = document.getElementById('filtreStatut').value;
        const res = await fetch(`/api/factures?statut=${statut}`);
        const data = await res.json();
        if(data.success) afficherFactures(data.data);
    } catch(e){ console.error(e); }
}

function afficherFactures(factures) {
    const tbody = document.getElementById('facturesTable');
    tbody.innerHTML = '';
    factures.forEach(f => {
        const tr = document.createElement('tr');
        const date = new Date(f.date_emission);
        let statutBadge = f.statut === 'payee' ? '✅ Payée' : f.statut === 'partielle' ? '⏳ Partielle' : '❌ Impayée';
        tr.innerHTML = `
            <td>${f.numero_facture}</td>
            <td>${date.toLocaleDateString('fr-FR')}</td>
            <td>${f.abonne}</td>
            <td>${f.montant_ttc.toLocaleString()} FCFA</td>
            <td>${f.montant_paye.toLocaleString()} FCFA</td>
            <td>${f.reste_a_payer.toLocaleString()} FCFA</td>
            <td>${statutBadge}</td>
            <td>
                <button class="btn btn-info" onclick="voirDetailsFacture(${f.id})">👁️</button>
                ${f.reste_a_payer>0?`<button class="btn btn-primary" onclick="ajouterPaiement(${f.id})">💰</button>`:''}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function chargerConsommationsNonFacturees() {
    const abId = document.getElementById('abonneFacture').value;
    if(!abId) return;
    try {
        const res = await fetch(`/api/factures/abonne/${abId}/non-facturees`);
        const data = await res.json();
        if(data.success) {
            const section = document.getElementById('consommationsSection');
            const liste = document.getElementById('consommationsList');
            if(data.data.length===0){ section.style.display='none'; return; }
            section.style.display='block';
            liste.innerHTML=''; consommationsSelectionnees=[];
            data.data.forEach(c=>{
                const div = document.createElement('div');
                div.innerHTML=`<label><input type="checkbox" value="${c.id}" onchange="calculerTotalFacture()"> ${c.produit} x${c.quantite} = ${c.montant_total.toLocaleString()} FCFA</label>`;
                liste.appendChild(div);
            });
        }
    } catch(e){ console.error(e); }
}

function calculerTotalFacture() {
    const checkboxes = document.querySelectorAll('#consommationsList input:checked');
    consommationsSelectionnees = Array.from(checkboxes).map(cb=>parseInt(cb.value));
    const total = checkboxes.length*1000;
    document.getElementById('totalFacture').textContent = total.toLocaleString();
}

async function creerFacture(e){
    e.preventDefault();
    if(consommationsSelectionnees.length===0) { alert('Sélectionnez au moins une consommation'); return; }
    const data = {
        abonne_id: parseInt(document.getElementById('abonneFacture').value),
        consommation_ids: consommationsSelectionnees,
        date_echeance: document.getElementById('dateEcheance').value,
        note: document.getElementById('noteFacture').value
    };
    try{
        const res = await fetch('/api/factures',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
        const result = await res.json();
        if(result.success){
            closeModal('createFactureModal');
            document.getElementById('factureForm').reset();
            chargerFactures();
        } else alert(result.error);
    } catch(e){ console.error(e); }
}

function voirDetailsFacture(id){ /* similaire à factures précédentes */ }

function ajouterPaiement(id){ window.location.href=`/paiements?facture_id=${id}`; }

function showModal(id){ document.getElementById(id).style.display='block'; }
function closeModal(id){ document.getElementById(id).style.display='none'; }

window.onclick = function(e){ if(e.target.classList.contains('modal')) e.target.style.display='none'; }
