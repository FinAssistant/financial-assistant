## 🛠️ Development Environment

- **Language**: TypeScript (`^5.0.0`)
- **Framework**: React JS (vite, react-router, redux-toolkit)
- **Styling**: Styled Components
- **Data Fetching**: RTK Query (https://redux-toolkit.js.org/rtk-query/overview)
- **Testing**: Jest + React Testing Library
- **Linting**: ESLint with `@typescript-eslint`
- **Package Manager**: `npm` (preferred)

## 🧱 Component Guidelines

- Use styled components
- Always keep the implementation as simple as possible
- Always check if we can reuse existing components or styles from our codebase and/or installed libraries

## Coding Best Practices

- **Early Returns**: Use to avoid nested conditions
- **Descriptive Names**: Use clear variable/function names (prefix handlers with "handle")
- **Constants Over Functions**: Use constants where possible
- **DRY Code**: Don't repeat yourself
- **Functional Style**: Prefer functional, immutable approaches when not verbose
- **Minimal Changes**: Only modify code related to the task at hand
- **Function Ordering**: Define composing functions before their components
- **TODO Comments**: Mark issues in existing code with "TODO:" prefix
- **Simplicity**: Prioritize simplicity and readability over clever solutions
- **Build Iteratively** Start with minimal functionality and verify it works before adding complexity
- **Run Tests**: Test your code frequently with realistic inputs and validate outputs
- **Functional Code**: Use functional and stateless approaches where they improve clarity
- **Clean logic**: Keep core logic clean and push implementation details to the edges
- **File Organization**: Balance file organization with simplicity - use an appropriate number of files for the project scale

## 📝 Code Style Standards

- Prefer arrow functions
- Annotate return types
- Always destructure props
- Avoid `any` type, use `unknown` or strict generics

## Code Quality

- Type hints required for all code
- Public APIs must have docstrings
- Functions must be focused and small
- Follow existing patterns exactly
- Line length: 88 chars maximum

## ⚙️ Dev Commands

- **Dev server**: `npm run dev`
- **Build**: `npm run build`
- **Lint**: `npm run lint`
- **Test**: `npx jest`
- **Generate API**: `npm run codegen:api`
