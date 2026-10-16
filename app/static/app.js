const element = (id) => document.getElementById(id);
const startTripForm = element("start-trip-form");
const finishTripForm = element("finish-trip-form");
let passengers = [];
let drivers = [];
let tripId = sessionStorage.getItem("tripId");

async function request(path, body) {
  const response = await fetch(path, body === undefined ? {} : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((issue) => `${issue.loc.at(-1)}: ${issue.msg}`).join(". ")
      : data.detail;
    const error = new Error(detail || "The request failed. Please try again.");
    error.status = response.status;
    throw error;
  }
  return data;
}

async function showTrip(trip) {
  const completed = trip.status === "COMPLETED";
  element("start-panel").hidden = true;
  element("trip-panel").hidden = false;
  element("trip-status").textContent = completed ? "3 / 3 · Completed" : "2 / 3 · In progress";
  element("trip-heading").textContent = completed ? "Trip completed" : "Trip in progress";
  element("trip-passenger").textContent = passengers.find((row) => row.id === trip.passenger_id)?.name || trip.passenger_id;
  const driver = drivers.find((row) => row.id === trip.driver_id);
  element("trip-driver").textContent = driver ? `${driver.name} · ${driver.vehicle_registration}` : trip.driver_id;
  element("trip-city").textContent = trip.city;
  element("trip-started").textContent = new Date(trip.started_at).toLocaleString();
  element("trip-id").textContent = trip.id;
  finishTripForm.hidden = completed;

  if (completed && element("receipt-panel").hidden) {
    if (!trip.receipt_id) throw new Error("The trip is completed, but its receipt is unavailable.");
    const receipt = await request(`/receipts/${trip.receipt_id}`);
    element("receipt-cost").textContent = `${receipt.cost} ${receipt.currency}`;
    element("receipt-number").textContent = receipt.receipt_number;
    element("receipt-issued").textContent = new Date(receipt.issued_at).toLocaleString();
    element("receipt-distance").textContent = `${trip.distance_meters.toLocaleString()} m`;
    element("receipt-panel").hidden = false;
  }
}

async function restoreTrip() {
  try {
    await showTrip(await request(`/trips/${tripId}`));
  } catch (error) {
    if (error.status === 404) {
      resetTrip();
      element("message").textContent = "That trip no longer exists. You can start another.";
    } else {
      throw error;
    }
  }
}

async function submit(form, action) {
  const fields = form.querySelector("fieldset");
  fields.disabled = true;
  form.querySelector("button").setAttribute("aria-busy", "true");
  element("message").textContent = "";
  try {
    await action();
  } catch (error) {
    element("message").textContent = error.message;
  } finally {
    fields.disabled = false;
    form.querySelector("button").removeAttribute("aria-busy");
  }
}

startTripForm.addEventListener("submit", (event) => {
  event.preventDefault();
  // Read the values before disabling the form controls.
  const data = Object.fromEntries(new FormData(startTripForm));
  data.pickup_latitude = Number(data.pickup_latitude);
  data.pickup_longitude = Number(data.pickup_longitude);
  submit(startTripForm, async () => {
    const trip = await request("/trips", data);
    tripId = trip.id;
    sessionStorage.setItem("tripId", tripId);
    await showTrip(trip);
    element("trip-heading").focus();
  });
});

finishTripForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(finishTripForm));
  for (const key of ["dropoff_latitude", "dropoff_longitude", "distance_meters"]) {
    data[key] = Number(data[key]);
  }
  // Keep cost as a string so the API receives the exact decimal value.
  submit(finishTripForm, async () => {
    await showTrip(await request(`/trips/${tripId}/finish`, data));
    element("trip-heading").focus();
  });
});

function resetTrip() {
  tripId = null;
  sessionStorage.removeItem("tripId");
  element("trip-panel").hidden = true;
  element("receipt-panel").hidden = true;
  element("start-panel").hidden = false;
  finishTripForm.reset();
  element("message").textContent = "";
  element("passenger").focus();
}

element("another-trip").addEventListener("click", resetTrip);

async function initialize() {
  try {
    [passengers, drivers] = await Promise.all([request("/passengers"), request("/drivers")]);
    for (const passenger of passengers) {
      element("passenger").add(new Option(passenger.name, passenger.id));
    }
    for (const driver of drivers) {
      element("driver").add(new Option(`${driver.name} · ${driver.vehicle_registration}`, driver.id));
    }
    if (!passengers.length || !drivers.length) {
      throw new Error("No passengers or drivers are available. Restart the app to load the demo records.");
    }
    startTripForm.querySelector("fieldset").disabled = false;
    element("message").textContent = "";
    if (tripId) await restoreTrip();
  } catch (error) {
    element("message").textContent = `${error.message} Reload the page to try again.`;
  }
}

initialize();
