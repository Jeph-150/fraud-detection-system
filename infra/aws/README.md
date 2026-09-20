# AWS Deployment Notes

Target: ECS/Fargate, with each containerized pipeline stage as its own
deployable service/task.

- Build and push each service image to ECR, e.g.
  `docker build -f ingestion/Dockerfile -t fraud-ingestion .` (likewise `scoring/` and `alerting/`).
  The scoring image bundles `scoring/model.pkl`, so train the model before building it.
- Ingestion (`POST /transactions`), scoring, and alerting (`GET /alerts`) are
  designed to be split into independent services/tasks so each can scale
  separately as load grows.
- SQLite is file-based and single-writer; it's fine for local/dev but does not
  support concurrent writers across multiple ECS tasks. Swap `DATABASE_URL`
  for a managed database (e.g. RDS) before running more than one API task.
