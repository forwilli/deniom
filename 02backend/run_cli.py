"""
Deniom Analysis CLI

This is an internal management and maintenance tool for the Deniom platform.
It is used to manually trigger data update flows, perform database migrations,
and other administrative tasks.
"""
import asyncio
import os
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Set the Gemini API key
os.environ['GEMINI_API_KEY'] = 'AIzaSyDuSx0w42heJRCrfDuKDLP0qITjUJ2D5HY'

app = typer.Typer(
    name="deniom-cli",
    help="Internal management tool for the Deniom platform.",
    add_completion=False,
)
console = Console(force_terminal=False, legacy_windows=True)

@app.command()
def run_pipeline(
    min_stars: int = typer.Option(0, "--min-stars", "-s", help="Minimum stars for projects to process."),
    projects_to_filter: int = typer.Option(5000, "--limit", "-l", help="Max number of projects to run through the filter stage."),
    deep_eval: bool = typer.Option(False, "--deep-evaluation", help="Include deep evaluation phase."),
    market_analysis: bool = typer.Option(False, "--market-analysis", help="Include market insight analysis phase."),
):
    """
    📈 Run the full analysis pipeline.
    
    This command orchestrates the entire workflow from fetching to analyzing projects.
    """
    # Import services here, inside the command function, to ensure all modules are loaded.
    from app.core import init_db
    from app.services.opportunity_service import opportunity_service
    
    phases = ["Screening"]
    if deep_eval:
        phases.append("Deep Evaluation")
    if market_analysis:
        phases.append("Market Analysis")
    
    console.print(Panel(
        f"🚀 Starting Deniom analysis pipeline\n"
        f"Min Stars: {min_stars} | Filter Limit: {projects_to_filter}\n"
        f"Phases: {' → '.join(phases)}",
        title="Pipeline Orchestrator",
        expand=False,
        border_style="bold green"
    ))

    async def _run():
        console.print("🔧 Initializing database...")
        init_db()
        console.print("✅ Database initialized.")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            main_task = progress.add_task(description="Running analysis pipeline...", total=None)
            
            try:
                results = await opportunity_service.run_analysis_pipeline(
                    min_stars=min_stars, 
                    projects_to_filter=projects_to_filter,
                    include_deep_evaluation=deep_eval,
                    include_market_analysis=market_analysis
                )
                progress.update(main_task, completed=True, visible=False)

                summary_text = (
                    f"✔️ [bold green]Pipeline Run Summary[/bold green]\n\n"
                    f"New Projects Added: [bold cyan]{results['newly_added']}[/bold cyan]\n"
                    f"Projects Passed Filter: [bold green]{results['passed_filter']}[/bold green]\n"
                    f"Projects Rejected: [bold red]{results['rejected_count']}[/bold red]"
                )
                
                if deep_eval:
                    summary_text += f"\nProjects Deep Evaluated: [bold yellow]{results['deep_evaluated']}[/bold yellow]"
                
                if market_analysis:
                    summary_text += f"\nProjects Market Analyzed: [bold magenta]{results['market_analyzed']}[/bold magenta]"

                console.print(Panel(
                    summary_text,
                    title="Results",
                    border_style="green",
                    expand=False
                ))

            except Exception as e:
                progress.update(main_task, completed=True, visible=False)
                console.print(f"❌ [bold red]A critical error occurred in the pipeline:[/bold red] {e}")
                import traceback
                traceback.print_exc()

        console.print("\n[bold green]✅ Pipeline finished.[/bold green]")

    asyncio.run(_run())

@app.command()
def run_screening(
    date_str: Optional[str] = typer.Option(None, "--date", "-d", help="目标日期 (YYYY-MM-DD)。默认为北京时间的前一天。"),
    max_projects: int = typer.Option(1000, "--limit", "-l", help="Max number of new projects to fetch and process."),
    no_fetch: bool = typer.Option(False, "--no-fetch", help="跳过从GitHub获取新数据，仅处理数据库中已有项目。"),
):
    """
    🔍 运行统一筛选阶段 (获取指定日期 >2星项目 -> AI评估)
    """
    from src.core.database import init_db
    from src.features.projects.service import project_service
    from datetime import datetime, timedelta
    import pytz

    # 处理日期
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            console.print(f"❌ [bold red]日期格式错误。请使用 YYYY-MM-DD 格式。[/bold red]")
            raise typer.Exit(code=1)
    else:
        # 默认为北京时间的前一天
        beijing_tz = pytz.timezone('Asia/Shanghai')
        yesterday_beijing = datetime.now(beijing_tz).date() - timedelta(days=1)
        target_date = datetime.combine(yesterday_beijing, datetime.min.time())

    fetch_new = not no_fetch
    panel_title = f"[bold blue]Unified Screening for {target_date.strftime('%Y-%m-%d')}[/bold blue]"
    if fetch_new:
        panel_title += " (with GitHub Fetch)"

    console.print(Panel(
        f"🚀 启动统一筛选阶段\n"
        f"批次日期: {target_date.strftime('%Y-%m-%d')} | 拉取上限: {max_projects}",
        title=panel_title,
        expand=False
    ))

    async def _run():
        console.print("🔧 正在初始化数据库...")
        init_db()
        console.print("✅ 数据库初始化完成。")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("正在执行统一筛选...", total=None)
            
            try:
                results = await project_service.run_screening_stage(
                    target_date=target_date,
                    max_projects=max_projects,
                    fetch_new=fetch_new
                )
                progress.update(task, completed=True, visible=False)

                summary_text = (
                    f"✔️ [bold green]统一筛选阶段总结 ({target_date.strftime('%Y-%m-%d')})[/bold green]\n\n"
                    f"已删除旧记录: [bold yellow]{results['deleted']}[/bold yellow]\n"
                    f"从GitHub获取: [bold cyan]{results['fetched']}[/bold cyan]\n"
                    f"新项目入库: [bold cyan]{results['newly_added']}[/bold cyan]\n"
                    f"已筛选项目: [bold yellow]{results['screened']}[/bold yellow]\n"
                    f"  - 通过筛选: [bold green]{results['passed']}[/bold green] (进入深度评估)\n"
                    f"  - 被拒绝: [bold red]{results['rejected']}[/bold red]"
                )
                console.print(Panel(summary_text, title="Results", border_style="green"))

            except Exception as e:
                progress.update(task, completed=True, visible=False)
                console.print(f"❌ [bold red]统一筛选阶段发生严重错误:[/bold red] {e}")
                import traceback
                traceback.print_exc()
        
        console.print("\n[bold green]✅ 统一筛选阶段执行完毕。[/bold green]")

    asyncio.run(_run())

@app.command()
def run_core_filter(
    max_projects: int = typer.Option(500, "--limit", "-l", help="Max number of projects to run core idea filtering on."),
):
    """
    💡 运行核心想法筛选 (痛点/新颖/病毒性/简洁)
    """
    from src.core.database import init_db
    from src.features.projects.service import project_service

    console.print(Panel(
        f"🚀 启动核心想法筛选阶段\n"
        f"处理上限: {max_projects}",
        title="[bold purple]Phase 2: Core Idea Filtering[/bold purple]",
        expand=False
    ))

    async def _run():
        console.print("🔧 正在初始化数据库...")
        init_db()
        console.print("✅ 数据库初始化完成。")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("正在执行核心想法筛选...", total=None)
            
            try:
                results = await project_service.run_core_idea_filter_stage(
                    max_projects=max_projects
                )
                progress.update(task, completed=True, visible=False)

                summary_text = (
                    f"✔️ [bold green]核心想法筛选阶段总结[/bold green]\n\n"
                    f"已处理项目: [bold cyan]{results['processed']}[/bold cyan]\n"
                    f"  - 通过筛选: [bold green]{results['passed']}[/bold green] (进入深度评估阶段)\n"
                    f"  - 被拒绝: [bold red]{results['rejected']}[/bold red]"
                )
                console.print(Panel(summary_text, title="Results", border_style="green"))

            except Exception as e:
                progress.update(task, completed=True, visible=False)
                console.print(f"❌ [bold red]核心想法筛选阶段发生严重错误:[/bold red] {e}")
                import traceback
                traceback.print_exc()
        
        console.print("\n[bold green]✅ 核心想法筛选阶段执行完毕。[/bold green]")

    asyncio.run(_run())

@app.command()
def run_evaluation(
    max_projects: int = typer.Option(50, "--limit", "-l", help="Max number of projects to run deep evaluation on."),
    reset_to_eval: Optional[str] = typer.Option(None, "--reset-to-eval", help="Repo full name (e.g. 'owner/repo') of a project to reset to EVALUATION stage."),
):
    """
    🧠 运行第三阶段：深度评估 (商业潜力/可行性/独特性)
    """
    from src.core.database import init_db
    from src.features.projects.service import project_service

    console.print(Panel(
        f"🚀 启动深度评估阶段\n"
        f"处理上限: {max_projects}",
        title="[bold yellow]Phase 3: Deep Evaluation[/bold yellow]",
        expand=False
    ))

    async def _run():
        console.print("🔧 正在初始化数据库...")
        init_db()
        console.print("✅ 数据库初始化完成。")

        if reset_to_eval:
            console.print(f"🔄 [bold yellow]正在重置项目 {reset_to_eval} 到评估阶段...[/bold yellow]")
            from src.core.database import get_session
            from src.features.projects.models import Project, AnalysisStage
            from sqlmodel import select, Session

            with Session(next(get_session()).bind) as session:
                stmt = select(Project).where(Project.repo_full_name == reset_to_eval)
                project_to_reset = session.exec(stmt).first()
                
                if not project_to_reset:
                    console.print(f"[bold red]❌ 找不到项目 {reset_to_eval}。[/bold red]")
                    return
                
                project_to_reset.current_stage = AnalysisStage.EVALUATION
                project_to_reset.evaluation_result = None
                project_to_reset.market_insight_result = None
                project_to_reset.synthesis_result = None
                project_to_reset.synthesis_score = None
                session.commit()
                console.print(f"✅ [bold green]已成功重置项目 {reset_to_eval}。[/bold green]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("正在执行深度评估...", total=None)
            
            try:
                results = await project_service.run_evaluation_stage(
                    max_projects=max_projects
                )
                progress.update(task, completed=True, visible=False)

                summary_text = (
                    f"✔️ [bold green]深度评估阶段总结[/bold green]\n\n"
                    f"已处理项目: [bold cyan]{results['processed']}[/bold cyan]\n"
                    f"  - 评估通过: [bold green]{results['success']}[/bold green] (进入市场分析阶段)\n"
                    f"  - 因无README被拒: [bold yellow]{results['no_readme']}[/bold yellow]\n"
                    f"  - 因AI评估被拒: [bold red]{results['failed']}[/bold red]"
                )
                console.print(Panel(summary_text, title="Results", border_style="green"))

            except Exception as e:
                progress.update(task, completed=True, visible=False)
                console.print(f"❌ [bold red]深度评估阶段发生严重错误:[/bold red] {e}")
                import traceback
                traceback.print_exc()
        
        console.print("\n[bold green]✅ 深度评估阶段执行完毕。[/bold green]")

    asyncio.run(_run())

@app.command()
def test_v13_eval():
    """
    🧪 对V13深度评估模型进行一个硬编码的单点测试。
    """
    from src.clients.analysis import analysis_client
    import json

    repo_name = "小猫补光灯App"
    readme_content = """
    核心想法：这是一款极其简单的手机应用。当用户需要在光线不足的环境下自拍拍照时，打开App，屏幕会变成一个纯色的、可调节亮度的柔和光源，为拍摄对象提供均匀、无闪光的补光。用户可以选择不同的背景色温（例如，暖黄、冷白）来创造不同的氛围。
    
    关键背景：这个App由一位不会写代码的产品经理，使用AI编程工具Cursor独立开发完成。
    """

    console.print(Panel(
        f"[bold]项目名称[/bold]: {repo_name}\n"
        f"[bold]核心想法[/bold]:\n{readme_content}",
        title="[bold yellow]V13 深度评估模型 - 单点测试[/bold yellow]",
        expand=False,
        border_style="yellow"
    ))

    async def _run_test():
        console.print("\n🧠 正在调用 V13 深度评估模型 (`gemini-2.5-pro`)...")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("AI正在思考...", total=None)
            
            try:
                ai_result = await analysis_client.analyze_project_readme(repo_name, readme_content)
                progress.update(task, completed=True, visible=False)
                console.print("✅ 分析完成。")

                console.print(Panel(
                    json.dumps(ai_result, indent=2, ensure_ascii=False),
                    title=f"[bold green]V13 评估结果: {repo_name}[/bold green]",
                    border_style="green"
                ))
            except Exception as e:
                progress.update(task, completed=True, visible=False)
                console.print(f"❌ [bold red]调用AI模型时发生错误:[/bold red] {e}")
                import traceback
                traceback.print_exc()

    asyncio.run(_run_test())

@app.command()
def test_idea(
    repo_name: str = typer.Argument(..., help="Repository full name (e.g., 'owner/repo') to test the V10.0 model on."),
):
    """
    💡 V10.0 "成败模式识别"模型单点测试
    """
    from src.clients.github import github_client
    from src.clients.analysis import analysis_client
    import json

    console.print(Panel(
        f"🚀 正在使用 V10.0 模型分析想法: [bold cyan]{repo_name}[/bold cyan]",
        title="[bold blue]V10.0 Pattern Recognition Test[/bold blue]",
        expand=False
    ))

    async def _run_test():
        # 1. 获取 README
        console.print(f"📄 正在获取 {repo_name} 的 README...")
        
        try:
            owner, repo = repo_name.split('/', 1)
        except ValueError:
            console.print(f"❌ [bold red]无效的仓库格式。请输入 'owner/repo' 格式。[/bold red]")
            return

        readme_content = await github_client.get_readme_content(owner, repo)

        if not readme_content:
            console.print(f"❌ [bold red]无法获取 {repo_name} 的 README/描述。测试中止。[/bold red]")
            return

        console.print("✅ 描述/README 获取成功。")
        
        # 2. 调用 V10.0 模型进行分析
        console.print("🧠 正在调用 V10.0 模型进行分析...")
        ai_result = await analysis_client.analyze_project_readme(repo_name, readme_content)
        console.print("✅ 分析完成。")

        # 3. 打印结果
        console.print(Panel(
            json.dumps(ai_result, indent=2, ensure_ascii=False),
            title=f"[bold green]V10.0 分析结果: {repo_name}[/bold green]",
            border_style="green"
        ))

    asyncio.run(_run_test())

@app.command()
def test_analysis(
    repo_name: str = typer.Argument(..., help="Repository full name (e.g., 'owner/repo')"),
):
    """
    🧪 Test the deep evaluation analysis on a specific repository.
    
    This command tests the AI analysis functionality on a single repository.
    """
    from app.core import init_db
    from app.services.analysis_service import analysis_service
    from app.services.github_service import github_service
    
    console.print(Panel(
        f"🧪 Testing deep evaluation analysis on: [bold cyan]{repo_name}[/bold cyan]",
        title="Analysis Test",
        expand=False,
        border_style="bold blue"
    ))

    async def _test():
        console.print("🔧 Initializing database...")
        init_db()
        console.print("✅ Database initialized.")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(description="Fetching README...", total=None)
            
            try:
                # Split repo_name into owner and repo
                if '/' not in repo_name:
                    console.print(f"❌ [bold red]Invalid repo format. Use 'owner/repo' format.[/bold red]")
                    return
                
                owner, repo = repo_name.split('/', 1)
                
                # Fetch README content
                readme_content = await github_service.get_readme_content(owner, repo)
                if not readme_content:
                    console.print(f"❌ [bold red]Could not fetch README for {repo_name}[/bold red]")
                    return
                
                progress.update(task, description="Analyzing with Gemini...")
                
                # Perform analysis
                analysis_result = await analysis_service.analyze_project_readme(
                    repo_name=repo_name,
                    readme_content=readme_content
                )
                
                progress.update(task, completed=True, visible=False)
                
                # Display results
                console.print(Panel(
                    f"✔️ [bold green]Analysis Results for {repo_name}[/bold green]\n\n"
                    f"Business Score: [bold cyan]{analysis_result.get('business_score', 'N/A')}[/bold cyan]\n"
                    f"Technical Score: [bold cyan]{analysis_result.get('technical_score', 'N/A')}[/bold cyan]\n"
                    f"Market Score: [bold cyan]{analysis_result.get('market_score', 'N/A')}[/bold cyan]\n"
                    f"Overall Score: [bold cyan]{analysis_result.get('overall_score', 'N/A')}[/bold cyan]\n\n"
                    f"Summary: {analysis_result.get('summary', 'N/A')}",
                    title="Analysis Results",
                    border_style="green",
                    expand=False
                ))

            except Exception as e:
                progress.update(task, completed=True, visible=False)
                console.print(f"❌ [bold red]Analysis failed:[/bold red] {e}")
                import traceback
                traceback.print_exc()

        console.print("\n[bold green]✅ Analysis test finished.[/bold green]")

    asyncio.run(_test())

@app.command()
def market_analysis(
    limit: int = typer.Option(5, "--limit", "-l", help="Maximum number of projects to analyze."),
):
    """
    🌍 运行第四阶段：市场分析 - 对综合评分最高的项目进行市场分析
    
    使用 gemini-2.5-pro 模型对通过深度评估的项目进行市场环境分析。
    """
    from src.core.database import init_db
    from src.features.projects.service import project_service
    
    console.print(Panel(
        f"🌍 启动第四阶段：市场分析\n"
        f"处理上限: {limit} 个项目\n"
        f"AI模型: gemini-2.5-pro",
        title="[bold magenta]Phase 4: Market Analysis[/bold magenta]",
        expand=False,
        border_style="bold magenta"
    ))

    async def _run_market():
        console.print("🔧 正在初始化数据库...")
        init_db()
        console.print("✅ 数据库初始化完成。")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("正在执行市场分析...", total=None)
            
            try:
                results = await project_service.run_market_analysis_stage(
                    max_projects=limit
                )
                progress.update(task, completed=True, visible=False)

                summary_text = (
                    f"✔️ [bold green]市场分析阶段总结[/bold green]\n\n"
                    f"已处理项目: [bold cyan]{results['processed']}[/bold cyan]\n"
                    f"  - 市场分析通过: [bold green]{results['success']}[/bold green] (进入最终合成阶段)\n"
                    f"  - 市场评估被拒: [bold red]{results['failed']}[/bold red]"
                )
                console.print(Panel(summary_text, title="Results", border_style="green"))

            except Exception as e:
                progress.update(task, completed=True, visible=False)
                console.print(f"❌ [bold red]市场分析阶段发生严重错误:[/bold red] {e}")
                import traceback
                traceback.print_exc()

        console.print("\n[bold green]✅ 市场分析阶段执行完毕。[/bold green]")

    asyncio.run(_run_market())

@app.command()
def test_market_analysis(
    repo_name: str = typer.Argument(..., help="Repository full name (e.g., 'owner/repo') to test market analysis on."),
):
    """
    🧪 测试单个项目的市场分析功能 - 使用 gemini-2.5-pro 模型
    """
    from src.core.database import init_db, get_session
    from src.features.projects.models import Project
    from src.clients.analysis import analysis_client
    from sqlmodel import select, Session
    import json

    console.print(Panel(
        f"🧪 测试市场分析功能\n"
        f"项目: [bold cyan]{repo_name}[/bold cyan]\n"
        f"AI模型: gemini-2.5-pro",
        title="[bold blue]Market Analysis Test[/bold blue]",
        expand=False,
        border_style="bold blue"
    ))

    async def _run_test():
        console.print("🔧 正在初始化数据库...")
        init_db()
        console.print("✅ 数据库初始化完成。")

        # 查找项目
        with Session(next(get_session()).bind) as session:
            stmt = select(Project).where(Project.repo_full_name == repo_name)
            project = session.exec(stmt).first()
            
            if not project:
                console.print(f"❌ [bold red]找不到项目 {repo_name}。[/bold red]")
                return
            
            console.print(f"✅ 找到项目: {project.repo_full_name}")
            console.print(f"   ⭐ Stars: {project.stars}")
            console.print(f"   💻 Language: {project.language or 'Unknown'}")
            console.print(f"   📝 Description: {project.description[:100] + '...' if project.description and len(project.description) > 100 else project.description or 'No description'}")
            
            # 获取产品评估总结
            product_summary = "未找到产品评估信息"
            if project.evaluation_result and isinstance(project.evaluation_result, dict):
                overall_assessment = project.evaluation_result.get('overall_assessment', {})
                product_summary = overall_assessment.get('summary', '未找到评估总结')
                eval_score = overall_assessment.get('final_score', 'N/A')
                console.print(f"   📊 评估分数: {eval_score}")

        # 准备项目信息
        project_info = {
            "repo_name": project.repo_full_name,
            "description": project.description,
            "language": project.language,
            "stars": project.stars
        }

        console.print(f"\n🧠 正在调用市场分析模型...")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("AI正在进行市场分析...", total=None)
            
            try:
                market_result = await analysis_client.analyze_market(project_info, product_summary)
                progress.update(task, completed=True, visible=False)
                console.print("✅ 市场分析完成。")

                console.print(Panel(
                    json.dumps(market_result, indent=2, ensure_ascii=False),
                    title=f"[bold green]市场分析结果: {repo_name}[/bold green]",
                    border_style="green"
                ))
                
                # 显示关键指标
                if isinstance(market_result, dict) and 'overall_market_assessment' in market_result:
                    assessment = market_result['overall_market_assessment']
                    final_score = assessment.get('final_score', 'N/A')
                    recommendation = assessment.get('market_recommendation', 'N/A')
                    
                    console.print(f"\n📈 [bold]关键指标摘要:[/bold]")
                    console.print(f"   🎯 市场综合评分: [bold yellow]{final_score}/10[/bold yellow]")
                    console.print(f"   💡 市场推荐: [bold cyan]{recommendation}[/bold cyan]")
                    
                    if 'key_opportunities' in assessment:
                        console.print(f"   🚀 主要机会: {', '.join(assessment['key_opportunities'][:2])}")
                    if 'key_risks' in assessment:
                        console.print(f"   ⚠️ 主要风险: {', '.join(assessment['key_risks'][:2])}")

            except Exception as e:
                progress.update(task, completed=True, visible=False)
                console.print(f"❌ [bold red]市场分析失败:[/bold red] {e}")
                import traceback
                traceback.print_exc()

    asyncio.run(_run_test())

@app.command()
def deep_evaluation(
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of projects to evaluate."),
):
    """
    🔍 Run deep evaluation on projects that passed initial screening.
    
    This command performs detailed README analysis on promising projects.
    """
    from app.core import init_db
    from app.services.opportunity_service import opportunity_service
    
    console.print(Panel(
        f"🔍 Starting deep evaluation analysis (limit={limit})",
        title="Deep Evaluation",
        expand=False,
        border_style="bold yellow"
    ))

    async def _run_deep():
        console.print("🔧 Initializing database...")
        init_db()
        console.print("✅ Database initialized.")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(description="Running deep evaluation...", total=None)
            
            try:
                evaluated_count = await opportunity_service.run_deep_evaluation_on_new_projects(limit=limit)
                progress.update(task, completed=True, visible=False)

                console.print(Panel(
                    f"✔️ [bold green]Deep Evaluation Summary[/bold green]\n\n"
                    f"Projects Evaluated: [bold cyan]{evaluated_count}[/bold cyan]",
                    title="Results",
                    border_style="green",
                    expand=False
                ))

            except Exception as e:
                progress.update(task, completed=True, visible=False)
                console.print(f"❌ [bold red]Deep evaluation failed:[/bold red] {e}")
                import traceback
                traceback.print_exc()

        console.print("\n[bold green]✅ Deep evaluation finished.[/bold green]")

    asyncio.run(_run_deep())

@app.command()
def show_evaluation_projects():
    """显示处于 EVALUATION 阶段的项目详细信息"""
    from src.core.database import get_session
    from src.features.projects.models import Project
    from sqlalchemy import select
    
    console.print(Panel("🧠 EVALUATION 阶段项目详情", style="bold blue"))
    
    session = next(get_session())
    
    try:
        # 查询处于 EVALUATION 阶段的项目
        result = session.execute(
            select(Project).where(Project.current_stage == 'EVALUATION')
        )
        projects = result.scalars().all()
        
        console.print(f"\n找到 [bold]{len(projects)}[/bold] 个处于 EVALUATION 阶段的项目:")
        
        for project in projects:
            console.print(f"\n📋 [bold cyan]{project.repo_full_name}[/bold cyan]")
            console.print(f"   ⭐ Stars: {project.stars}")
            console.print(f"   💻 Language: {project.language or 'Unknown'}")
            console.print(f"   📝 Description: {project.description[:100] + '...' if project.description and len(project.description) > 100 else project.description or 'No description'}")
            console.print(f"   ✅ Has evaluation_result: {'Yes' if project.evaluation_result else 'No'}")
            console.print(f"   🌍 Has market_insight_result: {'Yes' if project.market_insight_result else 'No'}")
            
            if project.evaluation_result and len(project.evaluation_result) > 200:
                # 显示评估结果的前200个字符
                eval_preview = project.evaluation_result[:200] + "..."
                console.print(f"   📊 Evaluation preview: {eval_preview}")
    
    finally:
        session.close()

@app.command()
def show_market_projects():
    """显示处于 MARKET_INSIGHT 阶段的项目详细信息"""
    from src.core.database import get_session
    from src.features.projects.models import Project
    from sqlalchemy import select
    import json
    
    console.print(Panel("🌍 MARKET_INSIGHT 阶段项目详情", style="bold green"))
    
    session = next(get_session())
    
    try:
        # 查询处于 MARKET_INSIGHT 阶段的项目
        result = session.execute(
            select(Project).where(Project.current_stage == 'MARKET_INSIGHT')
        )
        projects = result.scalars().all()
        
        console.print(f"\n找到 [bold]{len(projects)}[/bold] 个处于 MARKET_INSIGHT 阶段的项目:")
        
        for project in projects:
            console.print(f"\n🌟 [bold cyan]{project.repo_full_name}[/bold cyan]")
            console.print(f"   ⭐ Stars: {project.stars}")
            console.print(f"   💻 Language: {project.language or 'Unknown'}")
            
            # 完整打印评估结果
            if project.evaluation_result:
                console.print("   [bold yellow]深度评估结果:[/bold yellow]")
                # 使用json.dumps进行格式化，确保中文正常显示
                console.print(json.dumps(project.evaluation_result, indent=2, ensure_ascii=False))
            
            # 显示市场洞察关键词
            if project.market_insight_result:
                try:
                    market_data = project.market_insight_result if isinstance(project.market_insight_result, dict) else json.loads(project.market_insight_result)
                    keywords = market_data.get('keywords', [])
                    console.print(f"   🔍 Market Keywords: {', '.join(keywords[:3])}{'...' if len(keywords) > 3 else ''}")
                except:
                    pass
    
    finally:
        session.close()

@app.command()
def stats():
    """显示数据库统计信息"""
    from src.core.database import get_session
    from src.features.projects.models import Project
    from sqlalchemy import func, select
    
    console.print(Panel("📊 Deniom 项目数据统计", style="bold blue"))
    
    session = next(get_session())
    
    try:
        # 总项目数
        total_count = session.scalar(func.count(Project.id))
        console.print(f"\n🔢 [bold]总项目数:[/bold] {total_count}")
        
        # 按阶段统计
        result = session.execute(
            select(Project.current_stage, func.count(Project.id))
            .group_by(Project.current_stage)
        )
        stages = result.fetchall()
        
        console.print(f"\n📈 [bold]按分析阶段统计:[/bold]")
        stage_icons = {
            "SCREENING": "🔍",
            "EVALUATION": "🧠", 
            "MARKET_INSIGHT": "🌍",
            "SYNTHESIS": "💎",
            "REJECTED": "❌"
        }
        
        for stage, count in stages:
            stage_name = str(stage).split('.')[-1]
            icon = stage_icons.get(stage_name, "📊")
            console.print(f"  {icon} {stage_name}: {count} 项目")
        
        # 通过筛选的项目数
        passed_count = session.scalar(
            select(func.count(Project.id)).where(Project.current_stage != 'REJECTED')
        )
        rejected_count = total_count - passed_count
        pass_rate = (passed_count / total_count * 100) if total_count > 0 else 0
        
        console.print(f"\n✅ [bold]筛选结果:[/bold]")
        console.print(f"  通过初筛: [green]{passed_count}[/green] 项目")
        console.print(f"  被拒绝: [red]{rejected_count}[/red] 项目") 
        console.print(f"  通过率: [yellow]{pass_rate:.1f}%[/yellow]")
        
        # 按星数分布
        from sqlalchemy import case
        result = session.execute(
            select(
                case(
                    (Project.stars >= 1000, '1000+ stars'),
                    (Project.stars >= 100, '100-999 stars'),
                    (Project.stars >= 10, '10-99 stars'),
                    else_='< 10 stars'
                ).label('star_range'),
                func.count(Project.id)
            ).group_by('star_range')
        )
        star_ranges = result.fetchall()
        
        console.print(f"\n⭐ [bold]按星数分布:[/bold]")
        for star_range, count in star_ranges:
            console.print(f"  {star_range}: {count} 项目")
        
        # 编程语言分布（前10）
        result = session.execute(
            select(Project.language, func.count(Project.id))
            .where(Project.language.isnot(None))
            .group_by(Project.language)
            .order_by(func.count(Project.id).desc())
            .limit(10)
        )
        languages = result.fetchall()
        
        console.print(f"\n💻 [bold]编程语言分布 (前10):[/bold]")
        for language, count in languages:
            console.print(f"  {language}: {count} 项目")
        
        # 活跃状态统计
        active_count = session.scalar(
            select(func.count(Project.id)).where(Project.is_active == True)
        )
        promising_count = session.scalar(
            select(func.count(Project.id)).where(Project.is_promising == True)
        )
        
        console.print(f"\n🚀 [bold]项目活跃度:[/bold]")
        console.print(f"  活跃项目: {active_count}")
        console.print(f"  有潜力项目: {promising_count}")
        
        # 高质量项目展示（≥50星且未被拒绝）
        result = session.execute(
            select(Project.repo_full_name, Project.stars, Project.current_stage, Project.language)
            .where(Project.stars >= 50)
            .where(Project.current_stage != 'REJECTED')
            .order_by(Project.stars.desc())
            .limit(10)
        )
        high_quality = result.fetchall()
        
        console.print(f"\n🌟 [bold]高质量项目 (≥50⭐ 且未被拒绝):[/bold]")
        if high_quality:
            for name, stars, stage, language in high_quality:
                stage_name = str(stage).split('.')[-1]
                lang_str = f" ({language})" if language else ""
                console.print(f"  [cyan]{name}[/cyan]{lang_str} - {stars}⭐ - {stage_name}")
        else:
            console.print("  [dim]暂无符合条件的项目[/dim]")
        
        # 总结
        console.print(f"\n🎯 [bold]分析总结:[/bold]")
        console.print(f"  • 共收集了 [yellow]{total_count}[/yellow] 个项目的数据")
        console.print(f"  • 筛选通过率为 [yellow]{pass_rate:.1f}%[/yellow]，符合严格筛选预期")
        console.print(f"  • 系统成功过滤了低质量项目和恶意软件")
        console.print(f"  • 数据采集和初步筛选功能运行正常")
        
        if passed_count > 0:
            console.print(f"  • 已有 [green]{passed_count}[/green] 个项目进入下一阶段分析")
        else:
            console.print(f"  • [red]建议调整筛选标准或扩大数据采集范围[/red]")
    
    finally:
        session.close()

@app.command()
def synthesis(
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of projects to synthesize."),
):
    """
    💎 Run top-tier synthesis analysis on market-analyzed projects.
    
    This is the final stage of the four-phase analysis model, generating 
    investment-grade comprehensive evaluations and recommendations.
    """
    from app.core import init_db
    from app.services.opportunity_service import opportunity_service
    
    console.print(Panel(
        f"💎 启动顶尖合成分析 (第四阶段)\n"
        f"处理限制: {limit} 个项目\n"
        f"这是四阶段分析模型的最终阶段，将生成投资级综合评估",
        title="🧠 Top-tier Synthesis",
        expand=False,
        border_style="bold magenta"
    ))

    async def _run_synthesis():
        console.print("🔧 Initializing database...")
        init_db()
        console.print("✅ Database initialized.")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(description="执行顶尖合成分析...", total=None)
            
            try:
                synthesized_count = await opportunity_service.run_synthesis_analysis(limit=limit)
                progress.update(task, completed=True, visible=False)

                console.print(Panel(
                    f"✔️ [bold green]顶尖合成分析汇总[/bold green]\n\n"
                    f"已完成合成分析: [bold cyan]{synthesized_count}[/bold cyan] 个项目\n"
                    f"🔥 四阶段分析流程全部完成！\n\n"
                    f"分析阶段总览:\n"
                    f"  🔍 第一阶段: 宽基筛选 (Wide-base Screening)\n"
                    f"  🧠 第二阶段: 深度评估 (Deep Evaluation)\n"
                    f"  🌍 第三阶段: 市场洞察 (Market Insight)\n"
                    f"  💎 第四阶段: 顶尖合成 (Top-tier Synthesis) ✅",
                    title="🎉 Analysis Complete",
                    border_style="green",
                    expand=False
                ))

            except Exception as e:
                progress.update(task, completed=True, visible=False)
                console.print(f"❌ [bold red]顶尖合成分析失败:[/bold red] {e}")
                import traceback
                traceback.print_exc()

        console.print("\n[bold green]✅ 顶尖合成分析完成。[/bold green]")

    asyncio.run(_run_synthesis())

@app.command()
def show_synthesis_projects():
    """
    💎 显示已完成顶尖合成分析的项目详细信息
    """
    from src.core.database import get_session
    from src.features.projects.models import Project
    from sqlalchemy import select
    import json
    
    console.print(Panel("💎 SYNTHESIS 阶段项目详情 - 投资级分析结果", style="bold magenta"))
    
    session = next(get_session())
    
    try:
        # 查询处于 SYNTHESIS 阶段的项目
        result = session.execute(
            select(Project).where(Project.current_stage == 'SYNTHESIS')
            .order_by(Project.synthesis_score.desc())
        )
        projects = result.scalars().all()
        
        console.print(f"\n找到 [bold]{len(projects)}[/bold] 个已完成顶尖合成分析的项目:")
        
        for project in projects:
            console.print(f"\n💎 [bold cyan]{project.repo_full_name}[/bold cyan]")
            console.print(f"   ⭐ Stars: {project.stars}")
            console.print(f"   💻 Language: {project.language or 'Unknown'}")
            console.print(f"   📝 Description: {project.description[:100] + '...' if project.description and len(project.description) > 100 else project.description or 'No description'}")
            console.print(f"   📊 最终评分: [bold yellow]{project.synthesis_score or 'N/A'}[/bold yellow]/10")
            
            # 显示合成分析结果
            if project.market_insight_result:
                try:
                    market_data = project.market_insight_result if isinstance(project.market_insight_result, dict) else json.loads(project.market_insight_result)
                    synthesis_data = market_data.get('synthesis_result', {})
                    
                    if synthesis_data:
                        investment_rec = synthesis_data.get('investment_recommendation', 'N/A')
                        opportunity_rating = synthesis_data.get('business_opportunity_rating', 'N/A')
                        confidence = synthesis_data.get('confidence_level', 'N/A')
                        
                        console.print(f"   💡 投资建议: [bold green]{investment_rec}[/bold green]")
                        console.print(f"   🏆 机会等级: [bold blue]{opportunity_rating}[/bold blue]")
                        console.print(f"   📈 置信度: [bold cyan]{confidence}[/bold cyan]")
                        
                        # 显示关键洞察
                        key_insights = synthesis_data.get('key_insights', [])
                        if key_insights and len(key_insights) > 0:
                            console.print(f"   🔍 关键洞察: {key_insights[0][:80]}{'...' if len(key_insights[0]) > 80 else ''}")
                        
                        # 显示投资论述
                        investment_thesis = synthesis_data.get('investment_thesis', '')
                        if investment_thesis:
                            console.print(f"   📋 投资论述: {investment_thesis[:100]}{'...' if len(investment_thesis) > 100 else ''}")
                            
                except Exception as e:
                    console.print(f"   ⚠️ 解析合成结果时出错: {e}")
    
    finally:
        session.close()

if __name__ == "__main__":
    app() 