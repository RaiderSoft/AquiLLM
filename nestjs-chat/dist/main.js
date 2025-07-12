"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const core_1 = require("@nestjs/core");
const app_module_1 = require("./app.module");
const common_1 = require("@nestjs/common");
const path_1 = require("path");
const dotenv = require("dotenv");
require("reflect-metadata");
dotenv.config();
async function bootstrap() {
    const app = await core_1.NestFactory.create(app_module_1.AppModule);
    app.useGlobalPipes(new common_1.ValidationPipe());
    app.useStaticAssets((0, path_1.join)(__dirname, '..', 'public'));
    app.enableCors({
        origin: "*",
        methods: ["GET", "POST"],
        credentials: true,
    });
    const port = process.env.PORT || 3001;
    await app.listen(port);
    console.log(`NestJS Chat Server running on port ${port}`);
    console.log(`Frontend available at: http://localhost:${port}/index.html`);
}
bootstrap();
//# sourceMappingURL=main.js.map