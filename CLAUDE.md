# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands
- Backend: `cd aquillm && python manage.py runserver`
- Frontend: `cd react && npm run dev`
- Build frontend: `cd react && npm run build`
- TypeCheck frontend: `cd react && npm run typecheck`
- Run a single test: `cd aquillm && python -m pytest aquillm/tests/models_test.py::test_collection_creation -v`
- Run all tests: `cd aquillm && python -m pytest`
- Docker test: `docker-compose -f docker-compose-test.yml up`

## Code Style
- Python: Use Django naming conventions. Classes use PascalCase, functions/variables use snake_case
- TypeScript/React: Use React functional components with hooks. Components use PascalCase
- TypeScript: Use typed interfaces/props, avoid `any` types
- Error handling: Use try/catch blocks for async operations with meaningful error messages
- CSS: Tailwind is the primary styling framework
- State management: Use React's useState/useEffect for component state
- API calls: Use fetch API with proper error handling and type checking