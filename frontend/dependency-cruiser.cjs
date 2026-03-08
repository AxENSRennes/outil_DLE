/** @type {import("dependency-cruiser").IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: "no-local-imports-outside-src",
      severity: "error",
      comment:
        "Frontend source files must stay inside src/ and must not reach into backend or root files.",
      from: {
        path: "^src"
      },
      to: {
        dependencyTypes: ["local"],
        pathNot: "^src"
      }
    },
    {
      name: "no-shared-to-app-or-features",
      severity: "error",
      comment: "Shared frontend code must not depend on app wiring or feature modules.",
      from: {
        path: "^src/shared"
      },
      to: {
        path: "^src/(app|features)"
      }
    },
    {
      name: "no-cross-feature-imports",
      severity: "error",
      comment:
        "Feature modules must communicate through app wiring or shared contracts, not by deep importing each other.",
      from: {
        path: "^src/features/([^/]+)/"
      },
      to: {
        path: "^src/features/([^/]+)/",
        pathNot: "^src/features/$1/"
      }
    },
    {
      name: "no-non-test-imports-from-tests",
      severity: "error",
      comment: "Production code must not import frontend test modules.",
      from: {
        path: "^src/(?!.*\\.test\\.(ts|tsx)$).+"
      },
      to: {
        path: "\\.test\\.(ts|tsx)$"
      }
    },
    {
      name: "no-imports-from-backend",
      severity: "error",
      comment: "Frontend code must never import backend files.",
      from: {
        path: "^src"
      },
      to: {
        path: "^\\.\\./backend|^backend/"
      }
    }
  ],
  options: {
    tsConfig: {
      fileName: "tsconfig.json"
    },
    doNotFollow: {
      path: "node_modules"
    },
    exclude: {
      path: "node_modules"
    },
    reporterOptions: {
      dot: {
        collapsePattern: "node_modules/[^/]+"
      }
    }
  }
};
