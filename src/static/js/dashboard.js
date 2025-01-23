const activeUsersElement = document.querySelector("#activeUsers");
const platformEventsElement = document.querySelector("#platformEvents");
const communityPostsElement = document.querySelector("#communityPosts");

const monthlySignupsElement = document.querySelector("#monthlySignups");
const monthlyTransactionsElement = document.querySelector("#monthlyTransactions");

async function loadAnalysis() {
  const response = await fetch("/api/analysis");
  const data = await response.json();

  activeUsersElement.textContent = data.totalUsers;
  platformEventsElement.textContent = data.totalEvents;
  communityPostsElement.textContent = data.totalPosts;

  const monthlySignups = data.monthlySignups;
  const monthlyTransactions = data.monthlyTransactions;

  new Chart(monthlySignupsElement, {
    type: "line",
    data: {
      labels: monthlySignups.map((row) => row.month),
      datasets: [
        {
          label: "Signups per month",
          data: monthlySignups.map((row) => row.count),
        },
      ],
    },
    options: {
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });

  new Chart(monthlyTransactionsElement, {
    type: "line",
    data: {
      labels: monthlyTransactions.map((row) => row.month),
      datasets: [
        {
          label: "Transactions per month",
          data: monthlyTransactions.map((row) => row.count),
        },
      ],
    },
    options: {
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });
}

loadAnalysis();